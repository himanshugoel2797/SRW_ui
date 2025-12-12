"""Helpers for embedding visualizations using Matplotlib.

This module provides matplotlib embedding functions for plots in tkinter windows.
Falls back to simple in-memory representations for headless tests when matplotlib
is unavailable.

TODO: Consider extracting _DummyAx to a test utilities module if it grows.
"""
from typing import Optional, Callable, Any, Dict, Tuple


class _DummyAx:
    """Lightweight adapter that records plotting calls when matplotlib is
    unavailable. Keeps tests lightweight without matplotlib dependency.
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


def create_matplotlib_figure(parent: Optional[Any] = None, figsize: Tuple[int, int] = (5, 3),
                             draw_fn: Optional[Callable] = None) -> Dict[str, Any]:
    """Create a matplotlib figure and optionally embed it in a tkinter parent.

    Args:
        parent: Optional tkinter parent widget to embed the figure in
        figsize: Tuple of (width, height) for the figure
        draw_fn: Optional function to call with the axes for drawing

    Returns:
        Dict with keys: 'figure', 'canvas', 'toolbar' (canvas/toolbar are None if no parent)

    TODO: Review toolbar initialization and error handling for different backends.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import (
            FigureCanvasTkAgg,
            NavigationToolbar2Tk,
        )

        fig, ax = plt.subplots(figsize=figsize)
        
        if draw_fn is not None:
            draw_fn(ax)
        
        canvas = None
        toolbar = None
        
        if parent is not None:
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            try:
                toolbar = NavigationToolbar2Tk(canvas, parent)
                toolbar.update()
                toolbar.pack(side='top', fill='x')
            except Exception:
                toolbar = None
        
        return {'figure': fig, 'canvas': canvas, 'toolbar': toolbar}
    except Exception:
        ax = _DummyAx()
        if draw_fn is not None:
            draw_fn(ax)
        
        class _Fig:
            def __init__(self, ax):
                self.axes = [ax]

        fig = _Fig(ax)
        return {'figure': fig, 'canvas': None, 'toolbar': None}


def clear_matplotlib_figure(canvas, toolbar):
    """Clear matplotlib figure resources.

    Args:
        canvas: The FigureCanvasTkAgg instance to destroy
        toolbar: The NavigationToolbar2Tk instance to destroy
    """
    if canvas is not None:
        try:
            canvas.get_tk_widget().destroy()
        except Exception:
            pass
    if toolbar is not None:
        try:
            toolbar.destroy()
        except Exception:
            pass
