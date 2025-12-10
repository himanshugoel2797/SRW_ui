"""Helpers for embedding visualizations using Matplotlib.

This module provides a matplotlib embed helper for embedding plots
into tkinter windows. It falls back to simple in-memory representations
for headless tests when matplotlib is unavailable.
"""
from typing import Optional, Callable, Any


class _DummyAx:
    """Lightweight adapter that records plotting calls when matplotlib is
    unavailable. This keeps tests lightweight and avoids hard dependency
    on matplotlib in CI.

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


class MatplotlibEmbed:
    """Embedder that uses matplotlib if available, otherwise provides
    a headless adapter for tests.

    The `create_figure(draw_fn)` method will call draw_fn(ax) where `ax`
    is either a matplotlib axes object or a `_DummyAx` for headless operation.
    """

    def __init__(self, parent: Optional[Any] = None, figsize=(5, 3)):
        self.parent = parent
        self.figsize = figsize
        self.figure = None
        self.canvas = None
        self.toolbar = None

    def create_figure(self, draw_fn: Optional[Callable] = None):
        """Create a matplotlib figure and pass the axes to draw_fn.

        If matplotlib is not installed this will fall back to a dummy adapter
        so tests can assert behaviour without heavy plotting deps.
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import (
                FigureCanvasTkAgg,
                NavigationToolbar2Tk,
            )

            fig, ax = plt.subplots(figsize=self.figsize)
            
            if draw_fn is not None:
                draw_fn(ax)

            self.figure = fig
            
            # Embed into tkinter if parent is provided
            if self.parent is not None:
                canvas = FigureCanvasTkAgg(fig, master=self.parent)
                canvas.draw()
                canvas.get_tk_widget().pack(fill='both', expand=True)
                # Add a navigation toolbar for interactive plotting
                try:
                    toolbar = NavigationToolbar2Tk(canvas, self.parent)
                    # Ensure the toolbar initializes its state
                    toolbar.update()
                    # pack the toolbar above the canvas
                    toolbar.pack(side='top', fill='x')
                    self.toolbar = toolbar
                except Exception:
                    # If backend doesn't support toolbar or the environment
                    # is headless, skip adding toolbar.
                    self.toolbar = None
                self.canvas = canvas
            
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
        if self.canvas is not None:
            try:
                self.canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self.canvas = None
        if self.toolbar is not None:
            try:
                self.toolbar.destroy()
            except Exception:
                pass
            self.toolbar = None
        self.figure = None
