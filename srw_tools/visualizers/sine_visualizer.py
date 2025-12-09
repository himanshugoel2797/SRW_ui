"""Sine visualizer — moved from examples to visualizers.

This visualizer calculates a sine wave and returns numeric data when
matplotlib is not available; when matplotlib is present the GUI can
optionally render a plot via the GUI's richer output.
"""
from ..visualizer import Visualizer, register_visualizer


@register_visualizer
class SineVisualizer(Visualizer):
    name = 'sine'

    def process(self, data=None):
        try:
            import numpy as np
        except Exception:
            np = None

        amp = (data or {}).get('amplitude', 1.0)

        if np is None:
            x = [0]
            y = [0]
        else:
            x = np.linspace(0, 2 * np.pi, 200)
            y = amp * np.sin(x)

        # return numeric result so GUI can render it (or caller can plot)
        return {'x': (x.tolist() if hasattr(x, 'tolist') else list(x)),
                'y': (y.tolist() if hasattr(y, 'tolist') else list(y))}

    def parameters(self):
        return [
            {'name': 'amplitude', 'type': 'float', 'default': 1.0, 'label': 'Amplitude'},
        ]

    def view(self, parent=None, data=None):
        """Open a simple matplotlib window attached to the given parent.

        If parent is None, behave like process() and just return the data.
        """
        output = self.process(data)
        # try to render if a parent is provided and matplotlib is available
        if parent is None:
            return output

        # Use the MatplotlibEmbed helper so embedding logic is shared
        try:
            from ..gui_helpers import MatplotlibEmbed
        except Exception:
            # Can't embed; return the data to caller
            return output

        def draw(ax):
            ax.plot(output['x'], output['y'])
            ax.set_title(self.name)

        emb = MatplotlibEmbed(parent=parent, figsize=(5, 3))
        emb.create_figure(draw)
        return True
