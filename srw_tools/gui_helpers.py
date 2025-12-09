"""Helpers for embedding visualizations using HoloViews/Bokeh.

This module provides a small Holo/Bokeh embed helper which aims to be a
lightweight replacement for the earlier MatplotlibEmbed. It prefers the
event-driven `watchdog` and `bokeh` libraries when available; otherwise
it falls back to simple in-memory representations for headless tests.
"""
from typing import Optional, Callable, Any


class _DummyAx:
    """Lightweight adapter that records plotting calls when bokeh is
    unavailable. This keeps tests lightweight and avoids hard dependency
    on bokeh in CI.

    The adapter provides a minimal `plot`, `set_title` and `imshow`
    interface used by existing visualizers.
    """

    def __init__(self):
        self._lines = []
        self._images = []
        self._title = None

    def plot(self, x, y, *args, **kwargs):
        self._lines.append((list(x), list(y)))

    def set_title(self, t):
        self._title = t

    def imshow(self, grid, *args, **kwargs):
        self._images.append(grid)


class HoloEmbed:
    """Embedder that uses Bokeh (and HoloViews where appropriate) if
    available, otherwise provides a headless adapter for tests.

    The `create_figure(draw_fn)` method will call draw_fn(ax) where `ax`
    is either a Bokeh-aware adapter (supports `plot`, `imshow`, `set_title`)
    or a `_DummyAx` for headless operation.
    """

    def __init__(self, parent: Optional[Any] = None, figsize=(5, 3)):
        self.parent = parent
        self.figsize = figsize
        self.figure = None

    def create_figure(self, draw_fn: Optional[Callable] = None):
        """Create a Bokeh figure and pass an adapter to draw_fn.

        If Bokeh is not installed this will fall back to a dummy adapter
        so tests can assert behaviour without heavy plotting deps.
        """
        # Prefer to use bokeh if available
        try:
            from bokeh.plotting import figure as bokeh_figure

            width = int(self.figsize[0] * 100)
            height = int(self.figsize[1] * 100)
            fig = bokeh_figure(width=width, height=height)

            class _BokehAx:
                def __init__(self, fig):
                    self.fig = fig

                def plot(self, x, y, *args, **kwargs):
                    # bokeh uses line for 2D lines
                    try:
                        self.fig.line(x, y, *args, **kwargs)
                    except Exception:
                        # accept numpy arrays and convert
                        self.fig.line(list(x), list(y), *args, **kwargs)

                def set_title(self, t):
                    try:
                        self.fig.title.text = str(t)
                    except Exception:
                        pass

                def imshow(self, grid, *args, **kwargs):
                    # Bokeh image expects a 2D array inside a list
                    try:
                        self.fig.image(image=[grid], x=0, y=0, dw=1, dh=1)
                    except Exception:
                        # convert to lists if needed
                        self.fig.image(image=[list(map(list, grid))], x=0, y=0, dw=1, dh=1)

            ax = _BokehAx(fig)
            if draw_fn is not None:
                draw_fn(ax)

            self.figure = fig
            # embedding into tkinter is not implemented; visualizers handle UI
            return fig
        except Exception:
            # fallback: headless dummy adapter + simple figure-like object
            ax = _DummyAx()
            if draw_fn is not None:
                draw_fn(ax)
            # create a minimal figure-like object for tests
            class _Fig:
                def __init__(self, ax):
                    self.axes = [ax]

            fig = _Fig(ax)
            self.figure = fig
            return fig

    def clear(self):
        """Clear any internal figure references."""
        self.figure = None
