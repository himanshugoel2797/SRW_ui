"""Auto-loader for visualizer modules

Any python module placed under this package will be imported when the
package is imported, which triggers visualizer registration via
the `srw_tools.visualizer.register_visualizer` decorator.

This is written to be robust: module import errors are caught so a
broken optional visualizer won't prevent the package from loading.
"""
from importlib import import_module
from pathlib import Path
import pkgutil
import os

# Importing every module in this package so that any visualizer files
# register themselves with the central registry on import.
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
