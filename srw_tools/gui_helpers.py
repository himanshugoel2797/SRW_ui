"""Small helpers for embedding matplotlib figures into Tkinter.

This module provides a lightweight MatplotlibEmbed class that creates a
matplotlib Figure, attaches a Tk canvas and navigation toolbar when a
tkinter parent is supplied, and exposes helper methods to draw and clear
the figure. The implementation is robust when tkinter is not available
or when running headless (it will still create a Figure object).
"""
from typing import Optional, Callable, Any


class MatplotlibEmbed:
    """Helper to embed a matplotlib Figure inside a Tk parent.

    Usage:
      emb = MatplotlibEmbed(parent)
      fig = emb.create_figure(lambda ax: ax.plot(...))

    If `parent` is None, the helper still creates and returns a Figure
    (useful for headless tests or generating images without embedding).
    """

    def __init__(self, parent: Optional[Any] = None, figsize=(5, 3)):
        self.parent = parent
        self.figsize = figsize
        self.figure = None
        self.canvas = None
        self.toolbar = None

    def create_figure(self, draw_fn: Optional[Callable] = None):
        """Create a matplotlib Figure and optionally run draw_fn(ax).

        If tkinter is available and parent is set, this will create a
        FigureCanvasTkAgg and a NavigationToolbar2Tk. When parent is None
        or tkinter is unavailable, it will simply create and return the
        Figure instance.
        """
        # Delay-import matplotlib until used so tests and environments
        # without matplotlib still import this module.
        import matplotlib
        from matplotlib.figure import Figure

        # ensure a backend is set that can render offscreen if necessary
        try:
            matplotlib.use(matplotlib.get_backend(), force=False)
        except Exception:
            # ignore — backend may already be configured
            pass

        fig = Figure(figsize=self.figsize)
        ax = fig.add_subplot(111)

        if draw_fn is not None:
            try:
                draw_fn(ax)
            except Exception:
                # don't fail the caller; raise so calling code can handle it
                raise

        self.figure = fig

        # Try to attach to Tk only when parent supplied
        if self.parent is not None:
            try:
                import tkinter as _tk
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

                self.canvas = FigureCanvasTkAgg(fig, master=self.parent)
                self.canvas.draw()
                # pack canvas widget by default — caller can rearrange if desired
                self.canvas.get_tk_widget().pack(fill=_tk.BOTH, expand=True)

                # navigation toolbar
                self.toolbar = NavigationToolbar2Tk(self.canvas, self.parent)
                self.toolbar.update()
                try:
                    self.toolbar.pack(side=_tk.TOP, fill=_tk.X)
                except Exception:
                    # older versions use .pack on .tk
                    pass
            except Exception:
                # If tkinter or tkagg backends are not available, just return fig
                self.canvas = None
                self.toolbar = None

        return fig

    def clear(self):
        """Clear the current figure, if any."""
        if self.figure is not None:
            for ax in list(self.figure.axes):
                self.figure.delaxes(ax)
            self.figure = None
        if self.canvas is not None:
            try:
                widget = self.canvas.get_tk_widget()
                widget.destroy()
            except Exception:
                pass
            self.canvas = None
        if self.toolbar is not None:
            try:
                self.toolbar.destroy()
            except Exception:
                pass
            self.toolbar = None
