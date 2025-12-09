"""Helpers for discovering simulation scripts on disk.

This module extracts the simulation discovery logic previously embedded
in `gui.py` so other parts of the project can reuse it without importing
tkinter or GUI code.
"""
from pathlib import Path
import ast
from typing import Dict, Optional
import threading
import time


# unified watch handle type is defined below; remove earlier placeholder

class SimulationScriptManager:
    """Singleton manager for discovering simulation scripts on disk.

    The manager provides a simple interface: list_simulation_scripts(base_dir)
    and maintains an optional in-memory cache keyed by base_dir to avoid
    repeated disk scans when desirable. Using a manager object makes it
    easier to extend with additional behaviours later (caching, refresh,
    background scanning, etc.) while preserving the stateless module-level
    function for backwards compatibility.
    """

    def __init__(self):
        # cache maps base_dir (string or None) -> results dict
        self._cache: Dict[Optional[str], Dict[str, str]] = {}
        # watches map base_dir -> _WatchHandle
        self._watches: Dict[Optional[str], _WatchHandle] = {}

    def list_simulation_scripts(self, base_dir: Optional[str] = None, use_cache: bool = True) -> Dict[str, str]:
        """Discover simulation scripts under base_dir.

        If use_cache is True, results for the same base_dir may be returned
        from a simple in-memory cache. Use clear_cache() to invalidate.
        """
        key = base_dir or None
        if use_cache and key in self._cache:
            return self._cache[key]

        base = Path(base_dir or '.')
        results: Dict[str, str] = {}

        for p in base.rglob('*.py'):
            try:
                text = p.read_text(encoding='utf-8')
            except Exception:
                continue

            try:
                mod = ast.parse(text)
            except Exception:
                continue

            # require a set_optics function to be defined
            has_set_optics = any(isinstance(n, ast.FunctionDef) and n.name == 'set_optics' for n in mod.body)
            if not has_set_optics:
                continue

            # find assignments to varParam
            name_val = None
            for node in mod.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'varParam':
                            lst = node.value
                            if not isinstance(lst, ast.List):
                                continue
                            for elt in lst.elts:
                                if isinstance(elt, (ast.List, ast.Tuple)) and len(elt.elts) >= 3:
                                    # evaluate first and third if constants
                                    first = elt.elts[0]
                                    third = elt.elts[2]
                                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                                        if first.value == 'name' and isinstance(third, ast.Constant):
                                            name_val = third.value
                                            break
                            if name_val:
                                break
                if name_val:
                    break

            if name_val:
                try:
                    results[str(name_val)] = str(p.resolve())
                except Exception:
                    results[str(name_val)] = str(p)

        # store cache
        self._cache[key] = results
        return results

    def clear_cache(self, base_dir: Optional[str] = None):
        """Clear the cache for base_dir (or all if None)."""
        if base_dir is None:
            self._cache.clear()
        else:
            self._cache.pop(base_dir, None)

    def add_watch(self, base_dir: Optional[str], callback, interval: float = 0.5):
        """Start watching base_dir for changes and call callback(new_results)

        The watcher runs in a background daemon thread and invokes callback
        whenever the discovered set of scripts changes. If a watch for the
        same base_dir already exists it is replaced.
        """
        # normalize key
        key = base_dir or None

        # if there's already a watch, remove it first
        if key in self._watches:
            self.remove_watch(key)

        # Prefer using watchdog observers when available for efficient events
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class _Handler(FileSystemEventHandler):
                def __init__(self, manager: 'SimulationScriptManager', base_key, cb):
                    super().__init__()
                    self.manager = manager
                    self.base_key = base_key
                    self.cb = cb

                def _maybe_notify(self):
                    try:
                        curr = self.manager.list_simulation_scripts(self.base_key, use_cache=False)
                    except Exception:
                        curr = {}
                    prev = self.manager._cache.get(self.base_key)
                    if curr != prev:
                        self.manager._cache[self.base_key] = curr
                        try:
                            self.cb(curr)
                        except Exception:
                            pass

                def on_created(self, event):
                    if event.src_path.endswith('.py'):
                        self._maybe_notify()

                def on_modified(self, event):
                    if event.src_path.endswith('.py'):
                        self._maybe_notify()

                def on_deleted(self, event):
                    if event.src_path.endswith('.py'):
                        self._maybe_notify()

            # try to start observer
            base_path = str(Path(key or '.'))
            handler = _Handler(self, key, callback)
            observer = Observer()
            observer.schedule(handler, base_path, recursive=True)
            observer.daemon = True
            observer.start()

            self._watches[key] = _WatchHandle(observer=observer, use_observer=True)
            return
        except Exception:
            # fallback to polling-based watcher
            pass

        stop_event = threading.Event()

        def _watch_loop():
            prev = None
            # first populate prev with the current state (no change event)
            prev = self.list_simulation_scripts(key, use_cache=False)
            # sleep loop
            while not stop_event.is_set():
                try:
                    curr = self.list_simulation_scripts(key, use_cache=False)
                except Exception:
                    curr = {}

                if curr != prev:
                    # update cached state and notify
                    self._cache[key] = curr
                    try:
                        callback(curr)
                    except Exception:
                        # swallow exceptions from callbacks
                        pass
                    prev = curr

                # wait with timeout so we can shutdown quickly
                stop_event.wait(interval)

        th = threading.Thread(target=_watch_loop, daemon=True)
        th.start()
        self._watches[key] = _WatchHandle(thread=th, stop_event=stop_event, use_observer=False)

    def remove_watch(self, base_dir: Optional[str]):
        """Stop watching base_dir if a watcher exists."""
        key = base_dir or None
        h = self._watches.pop(key, None)
        if h is not None:
            if h.use_observer and h.observer is not None:
                try:
                    h.observer.stop()
                except Exception:
                    pass
                try:
                    h.observer.join(timeout=1.0)
                except Exception:
                    pass
            else:
                # polling thread
                if h.stop_event is not None:
                    h.stop_event.set()
                if h.thread is not None:
                    try:
                        h.thread.join(timeout=1.0)
                    except Exception:
                        pass

    def list_watches(self):
        """Return a list of currently watched base_dir keys."""
        return list(self._watches.keys())

    def stop_all_watches(self):
        """Stop all active watchers and clear internal watch registry."""
        keys = list(self._watches.keys())
        for k in keys:
            self.remove_watch(k)


# singleton instance used by callers
# singleton instance used by callers (renamed to `script_manager`)
script_manager = SimulationScriptManager()

class _WatchHandle:
    def __init__(self, thread=None, stop_event=None, observer=None, use_observer=False):
        self.thread = thread
        self.stop_event = stop_event
        self.observer = observer
        self.use_observer = use_observer


# Module intentionally does not provide a top-level helper function; use
# the `script_manager` singleton instead to obtain simulation scripts.
