"""SRW UI tools package

This package contains small, maintainable utilities for running SRW
simulation workflows: an RPC server, simple git helpers, and a visualizer
base class. Keep it tiny and dependency-free.
"""

__all__ = ["rpc_server", "git_helper", "visualizer", "cli", "gui", "nativelib"]

# Import the visualizers package so drop-in visualizer modules register on
# package import (keep resilient to missing optional deps by ignoring errors).
try:
	from . import visualizers  # type: ignore
except Exception:
	pass

try:
    from . import nativelib  # expose top-level api for native helpers
except Exception:
    pass
