"""Base Runner class for command execution backends.

This package contains different runner implementations for executing
shell commands and file operations in various environments.
"""
from importlib import import_module
from pathlib import Path
import pkgutil

# Import every runner module in this package so that their classes
# register themselves with the central runner registry on import.
_this_dir = Path(__file__).parent

for finder, name, ispkg in pkgutil.iter_modules([str(_this_dir)]):
    # ignore private modules starting with underscore
    if name.startswith('_'):
        continue
    module_name = f"{__name__}.{name}"
    try:
        import_module(module_name)
    except Exception:
        # keep the package usable even if individual visualizers fail
        # during import (e.g., missing optional deps)
        pass
