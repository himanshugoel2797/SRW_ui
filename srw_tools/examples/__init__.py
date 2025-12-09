"""Examples package for srw_tools.

Import example visualizers so they register on package import.
Make imports optional to keep the package usable without optional deps.
"""
try:
    from . import sample_visualizer  # type: ignore
except Exception:
    # optional deps may be missing; that's fine for a minimal install
    pass
