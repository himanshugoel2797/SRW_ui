"""Example visualizer placed under the new visualizers package.

It registers a tiny visualizer called 'square' so tests can confirm
auto-loading works.
"""
from ..visualizer import Visualizer, register_visualizer
import tkinter as tk

@register_visualizer
class SquareVisualizer(Visualizer):
    name = 'square'

    def local_process(self, data=None):
        # produce a simple numeric grid rather than requiring external deps
        size = (data or {}).get('size', 4)
        grid = [[1 if (i % 2 == 0 and j % 2 == 0) else 0 for j in range(size)] for i in range(size)]
        return {'grid': grid}

    def parameters(self):
        return [
            {'name': 'size', 'type': 'int', 'default': 4, 'label': 'Grid size'},
        ]

    def view(self, data=None):
        """Display the grid as an image when running in a GUI, otherwise return data."""
        output = self.process(data)

        # Use the HoloEmbed helper for consistent embedding
        try:
            from ..gui_helpers import HoloEmbed
        except Exception:
            return output

        def draw(ax):
            ax.imshow(output['grid'], cmap='gray')
            ax.set_title(self.name)

        win = tk.Toplevel()
        win.title(self.name)

        emb = HoloEmbed(figsize=(4, 4))
        emb.create_figure(draw)
        return True
