"""SRW UI tools package

This package contains small, maintainable utilities for running SRW
simulation workflows: an RPC server, simple git helpers, and a visualizer
base class. Keep it tiny and dependency-free.
"""

__all__ = ["rpc_server", "git_helper", "visualizer"]

# try to import example visualizers (optional) so they register automatically
try:
	# keep this import optional and resilient to missing optional deps
	from . import examples  # type: ignore
	# import common visualizers directory so files placed there register
	from . import visualizers  # type: ignore
except Exception:
	pass
