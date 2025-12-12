"""Helpers for discovering simulation scripts on disk.

Provides functions for finding and loading simulation scripts with
optional caching and filesystem watching capabilities.
"""
from pathlib import Path
import ast
import importlib.util
import sys
import uuid
from typing import Dict, Optional, Any, Callable, Tuple
import tempfile

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Module-level cache and watches
_cache: Dict[Tuple[Optional[str], str], Dict[str, str]] = {}
_watches: Dict[Optional[str], Any] = {}


class _WatchHandle:
    """Internal handle for filesystem watches."""
    def __init__(self, thread=None, stop_event=None, observer=None, use_observer=False):
        self.thread = thread
        self.stop_event = stop_event
        self.observer = observer
        self.use_observer = use_observer
class _WatchHandle:
    """Internal handle for filesystem watches."""
    def __init__(self, thread=None, stop_event=None, observer=None, use_observer=False):
        self.thread = thread
        self.stop_event = stop_event
        self.observer = observer
        self.use_observer = use_observer


def list_simulation_scripts(base_dir: Optional[str] = None, use_cache: bool = True, 
                            key_by: str = 'path') -> Dict[str, str]:
    """Discover simulation scripts under base_dir.

    Returns a dict mapping script path -> display name (or name -> path if key_by='name').

    Args:
        base_dir: Directory to scan for scripts (defaults to current directory)
        use_cache: Whether to use cached results
        key_by: 'path' for path->name mapping, 'name' for name->path mapping

    Returns:
        Dict mapping paths to names or names to paths depending on key_by
    """
    cache_key = (base_dir or None, key_by)
    if use_cache and cache_key in _cache:
        return _cache[cache_key]

    base = Path(base_dir or '.')
    results: Dict[str, str] = {}

    for p in base.rglob('*.py'):
        try:
            info = load_script(str(p))
        except Exception:
            continue

        if not info.get('set_optics'):
            continue

        name_val = None
        mod = info.get('module')
        if mod is not None and hasattr(mod, 'varParam') and mod.varParam:
            for vp in mod.varParam:
                if vp[0] == 'name' and len(vp) >= 2:
                    name_val = str(vp[2])
                    break

        if not name_val:
            name_val = p.stem

        try:
            results[str(p.resolve())] = str(name_val)
        except Exception:
            results[str(p)] = str(name_val)

    final_results = results
    if key_by == 'name':
        inv = {}
        for pth, name in results.items():
            if name not in inv:
                inv[name] = pth
        final_results = inv

    _cache[cache_key] = final_results
    return final_results


def load_script(path: str) -> Dict[str, Any]:
        """Load a simulation script and return info about it.

        Returns dict with keys: path, varParam, set_optics, module
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)

        info = {'path': str(p.resolve()), 'varParam': None, 'set_optics': None, 'module': None}

        module_name = f"_srw_script_{uuid.uuid4().hex}"
        try:
            try:
                src_text = p.read_text(encoding='utf-8')
            except Exception:
                src_text = None

            def _is_main_if(node: ast.If) -> bool:
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
                # Prefer `varParam` attribute name; fall back to `varParam`
                if hasattr(mod, 'varParam'):
                    info['varParam'] = getattr(mod, 'varParam')
                elif hasattr(mod, 'varParam'):
                    info['varParam'] = getattr(mod, 'varParam')
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


def get_varParam(path: str) -> Optional[Any]:
    """Return the varParam list for a given script path if available."""
    info = load_script(path)
    return info.get('varParam')


def get_set_optics(path: str) -> Optional[Callable]:
    """Return a callable handle to the script's set_optics function."""
    info = load_script(path)
    return info.get('set_optics')


def clear_cache(base_dir: Optional[str] = None):
    """Clear the cache for base_dir (or all if None)."""
    global _cache
    if base_dir is None:
        _cache.clear()
    else:
        keys_to_remove = [k for k in _cache.keys() if k[0] == base_dir]
        for key in keys_to_remove:
            _cache.pop(key, None)


def add_watch(base_dir: Optional[str], callback: Callable, interval: float = 0.5):
    """Start watching base_dir for changes and call callback(new_results).

    The watcher runs in a background daemon thread and invokes callback
    whenever the discovered set of scripts changes.
    """
    key = base_dir or None

    if key in _watches:
        remove_watch(key)

    class _Handler(FileSystemEventHandler):
        def __init__(self, base_key, cb):
            super().__init__()
            self.base_key = base_key
            self.cb = cb

        def _maybe_notify(self):
            try:
                curr = list_simulation_scripts(self.base_key, use_cache=False)
            except Exception:
                curr = {}
            cache_key = (self.base_key, 'path')
            prev = _cache.get(cache_key)
            if curr != prev:
                _cache[cache_key] = curr
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

    base_path = str(Path(key or '.'))
    handler = _Handler(key, callback)
    observer = Observer()
    observer.schedule(handler, base_path, recursive=True)
    observer.daemon = True
    observer.start()

    _watches[key] = _WatchHandle(observer=observer, use_observer=True)


def remove_watch(base_dir: Optional[str]):
    """Stop watching base_dir if a watcher exists."""
    key = base_dir or None
    h = _watches.pop(key, None)
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
            if h.stop_event is not None:
                h.stop_event.set()
            if h.thread is not None:
                try:
                    h.thread.join(timeout=1.0)
                except Exception:
                    pass


def list_watches():
    """Return a list of currently watched base_dir keys."""
    return list(_watches.keys())


def stop_all_watches():
    """Stop all active watchers and clear internal watch registry."""
    keys = list(_watches.keys())
    for k in keys:
        remove_watch(k)
