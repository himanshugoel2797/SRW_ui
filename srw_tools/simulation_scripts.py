"""Helpers for discovering simulation scripts on disk.

This module extracts the simulation discovery logic previously embedded
in `gui.py` so other parts of the project can reuse it without importing
tkinter or GUI code.
"""
from pathlib import Path
import ast
import importlib.util
import sys
import uuid
from typing import Dict, Optional, Any
import threading
import tempfile

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

    def list_simulation_scripts(self, base_dir: Optional[str] = None, use_cache: bool = True, key_by: str = 'path') -> Dict[str, str]:
        """Discover simulation scripts under base_dir.

        Returns a dict mapping script `path` -> display `name`.

        The `key_by` parameter controls which mapping is returned: by
        default (`key_by='path'`) a mapping of path->name is returned.
        If `key_by='name'` the mapping `name->path` is returned instead.

        If use_cache is True, results for the same base_dir may be returned
        from a simple in-memory cache. Use clear_cache() to invalidate.
        """
        cache_key = (base_dir or None, key_by)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        base = Path(base_dir or '.')
        results: Dict[str, str] = {}

        for p in base.rglob('*.py'):
            # Use the module loader to import the script and extract the
            # readable name and set_optics function. We accept executing
            # the script module because scripts are user-provided and need
            # to be able to run code to set up their configuration.
            try:
                info = self.load_script(str(p))
            except Exception:
                continue

            # Skip scripts that don't expose a set_optics function
            if not info.get('set_optics'):
                continue

            # Determine human-friendly name: prefer `display_name` or
            # module `name`, fall back to varParams `name` entry, and finally
            # fallback to filename stem.
            name_val = None
            mod = info.get('module')
            if mod is not None:
                name_val = getattr(mod, 'display_name', None) or getattr(mod, 'name', None)

            if not name_val:
                vp = info.get('varParams')
                if isinstance(vp, (list, tuple)):
                    for row in vp:
                        try:
                            if isinstance(row, (list, tuple)) and len(row) >= 3 and row[0] == 'name':
                                name_val = row[2]
                                break
                        except Exception:
                            continue

            if not name_val:
                name_val = p.stem

            try:
                results[str(p.resolve())] = str(name_val)
            except Exception:
                results[str(p)] = str(name_val)

        # If caller wants name->path mapping, invert the dict.
        final_results = results
        if key_by == 'name':
            inv = {}
            for pth, name in results.items():
                # prefer first occurrence when names conflict
                if name not in inv:
                    inv[name] = pth
            final_results = inv

        # store cache keyed by base_dir and key_by
        self._cache[cache_key] = final_results
        return final_results

    def load_script(self, path: str):
        """Load a simulation script and return info about it.

        The returned dictionary contains:
        - 'path': resolved path to the script
        - 'varParam': value parsed from the script if available (list), or None
        - 'set_optics': callable function object if present (imported module), or None
        - 'module': the imported module object (or None)

        We will try to extract `varParam` safely via AST literal parsing to
        avoid executing arbitrary script code. If `varParam` cannot be
        extracted as a literal, we fall back to importing the module to
        retrieve the runtime value. To obtain a callable handle for
        `set_optics` we import the module in a dedicated namespace and
        return the reference.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)

        info = {'path': str(p.resolve()), 'varParams': None, 'set_optics': None, 'module': None}

        # Import module to get set_optics and varParams. We sanitize the
        # script before executing to remove any top-level calls to
        # `main()` or `epilogue()` as well as `if __name__ == '__main__'`
        # blocks that would invoke them. This reduces accidental
        # side-effects at import time while still executing module-level
        # initialization that the script intentionally performs.
        # Create a unique module name to avoid clobbering sys.modules
        module_name = f"_srw_script_{uuid.uuid4().hex}"
        try:
            # Read file text
            try:
                src_text = p.read_text(encoding='utf-8')
            except Exception:
                src_text = None

            # Sanitize code via AST: remove top-level calls to `main()` and
            # `epilogue()` as well as if __name__ == '__main__' blocks.
            def _is_main_if(node: ast.If) -> bool:
                # Check for: if __name__ == '__main__':
                try:
                    if isinstance(node.test, ast.Compare):
                        # Check for patterns like: __name__ == '__main__' OR
                        # '__main__' == __name__ (either order)
                        left = node.test.left
                        comps = node.test.comparators
                        if len(comps) >= 1:
                            comp = comps[0]
                            # pattern: __name__ == '__main__'
                            if isinstance(left, ast.Name) and left.id == '__name__' and isinstance(comp, (ast.Constant, ast.Str)):
                                val = getattr(comp, 'value', None)
                                if val == '__main__':
                                    return True
                            # pattern: '__main__' == __name__
                            if isinstance(left, (ast.Constant, ast.Str)) and getattr(left, 'value', None) == '__main__' and isinstance(comp, ast.Name) and comp.id == '__name__':
                                return True
                    return False
                except Exception:
                    return False

            class _SanitizeTransformer(ast.NodeTransformer):
                def visit_Module(self, node: ast.Module) -> Any:
                    new_body = []
                    for child in node.body:
                        # Remove simple expressions that call main() or epilogue()
                        if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                            func = child.value.func
                            if isinstance(func, ast.Name) and func.id in ('main', 'epilogue'):
                                continue
                        # Remove `if __name__ == '__main__'` blocks entirely
                        if isinstance(child, ast.If) and _is_main_if(child):
                            continue
                        # Otherwise keep the node (and possibly visit nested nodes)
                        new_body.append(self.visit(child))
                    node.body = new_body
                    return node

            sanitized_path = None
            if src_text is not None:
                try:
                    parsed = ast.parse(src_text)
                    parsed = _SanitizeTransformer().visit(parsed)
                    ast.fix_missing_locations(parsed)
                    # compile and write to a temp file in the script directory so
                    # relative imports keep working. Use a unique file name.
                    san_name = f"_srw_sanitized_{uuid.uuid4().hex}.py"
                    tmp_dir = Path(tempfile.mkdtemp(prefix='srw_sanitized_'))
                    tmp_path = tmp_dir / san_name
                    # Write source from AST back to file
                    try:
                        code = compile(parsed, str(tmp_path), 'exec')
                        # Since we used compile with filename tmp_path, write
                        # the original source text for better tracebacks. We'll
                        # write the sanitized source to the temp file directly
                        # using ast.unparse when available.
                        try:
                            sanitized_text = ast.unparse(parsed)
                        except Exception:
                            # Fallback: if ast.unparse isn't available (older
                            # Pythons), just use original text.
                            sanitized_text = src_text
                        tmp_path.write_text(sanitized_text, encoding='utf-8')
                        sanitized_path = tmp_path
                    except Exception:
                        sanitized_path = None
                except Exception:
                    sanitized_path = None

            load_path = str(sanitized_path or p)
            # Temporarily ensure the original script directory is on sys.path so
            # relative imports and package resources can be resolved correctly.
            original_dir = str(p.parent.resolve())
            inserted_sys_path = False
            if original_dir not in sys.path:
                sys.path.insert(0, original_dir)
                inserted_sys_path = True
            spec = importlib.util.spec_from_file_location(module_name, load_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                # Do not override an existing module name — remove if created
                sys.modules[module_name] = mod
                try:
                    spec.loader.exec_module(mod)
                finally:
                    try:
                        sys.modules.pop(module_name, None)
                    except Exception:
                        pass
                    if inserted_sys_path:
                        try:
                            sys.path.remove(original_dir)
                        except Exception:
                            pass
                info['module'] = mod
                # Pull set_optics callable if present
                so = getattr(mod, 'set_optics', None)
                if callable(so):
                    info['set_optics'] = so
                # Prefer `varParams` attribute name; fall back to `varParam`
                if hasattr(mod, 'varParams'):
                    info['varParams'] = getattr(mod, 'varParams')
                elif hasattr(mod, 'varParam'):
                    info['varParams'] = getattr(mod, 'varParam')
        except Exception:
            # Import failed — return what we could find
            pass
        finally:
            # Clean up the temporary sanitized file if we created one
            try:
                if sanitized_path is not None and sanitized_path.exists():
                    sanitized_path.unlink()
                    # attempt to remove the directory containing it
                    try:
                        parent_dir = sanitized_path.parent
                        if parent_dir.exists():
                            parent_dir.rmdir()
                    except Exception:
                        pass
            except Exception:
                pass

        return info

    def get_varParams(self, path: str):
        """Return the varParams list for a given script path if available.

        This will import the module and return its `varParams`/`varParam`
        attribute. If not present, returns None.
        """
        info = self.load_script(path)
        return info.get('varParams')

    def get_set_optics(self, path: str):
        """Return a callable handle to the script's `set_optics` function.

        If the function is not present, returns None.
        """
        info = self.load_script(path)
        return info.get('set_optics')

    def clear_cache(self, base_dir: Optional[str] = None):
        """Clear the cache for base_dir (or all if None)."""
        if base_dir is None:
            self._cache.clear()
        else:
            # Remove all cache entries for this base_dir (with any key_by value)
            keys_to_remove = [k for k in self._cache.keys() if k[0] == base_dir]
            for key in keys_to_remove:
                self._cache.pop(key, None)

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
                    cache_key = (self.base_key, 'path')
                    prev = self.manager._cache.get(cache_key)
                    if curr != prev:
                        self.manager._cache[cache_key] = curr
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
            cache_key = (key, 'path')
            # sleep loop
            while not stop_event.is_set():
                try:
                    curr = self.list_simulation_scripts(key, use_cache=False)
                except Exception:
                    curr = {}

                if curr != prev:
                    # update cached state and notify
                    self._cache[cache_key] = curr
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
script_manager = SimulationScriptManager()

class _WatchHandle:
    def __init__(self, thread=None, stop_event=None, observer=None, use_observer=False):
        self.thread = thread
        self.stop_event = stop_event
        self.observer = observer
        self.use_observer = use_observer
