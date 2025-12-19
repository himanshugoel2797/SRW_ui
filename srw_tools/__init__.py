"""SRW UI tools package

This package contains small, maintainable utilities for running SRW
simulation workflows: SSH helpers and a visualizer base class. Keep it tiny and dependency-free.
"""

__all__ = ["ssh_helper", "visualizer", "cli", "gui", "nativelib", "runner_registry", "parameter_widgets", "simulation_scripts", "folder_utils", "gui_helpers"]

# Import the visualizers package so drop-in visualizer modules register on
# package import (keep resilient to missing optional deps by ignoring errors).
try:
    from . import visualizers  # type: ignore
except Exception:
    pass

try:
    from . import runners  # expose top-level api for runner implementations
except Exception:
    pass

try:
    from . import nativelib  # expose top-level api for native helpers
except Exception:
    pass
