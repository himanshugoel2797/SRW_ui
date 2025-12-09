"""Example visualizer placed under the new visualizers package.

It registers a tiny visualizer called 'square' so tests can confirm
auto-loading works.
"""
from ..visualizer import Visualizer, register_visualizer


@register_visualizer
class SquareVisualizer(Visualizer):
    name = 'square'

    def process(self, data=None):
        # produce a simple numeric grid rather than requiring external deps
        size = (data or {}).get('size', 4)
        grid = [[1 if (i % 2 == 0 and j % 2 == 0) else 0 for j in range(size)] for i in range(size)]
        return {'grid': grid}

    def parameters(self):
        return [
            {'name': 'size', 'type': 'int', 'default': 4, 'label': 'Grid size'},
        ]

    def view(self, parent=None, data=None):
        """Display the grid as an image if parent provided, otherwise return data."""
        output = self.process(data)
        if parent is None:
            return output

        # Use the MatplotlibEmbed helper for consistent embedding
        try:
            from ..gui_helpers import MatplotlibEmbed
        except Exception:
            return output

        def draw(ax):
            ax.imshow(output['grid'], cmap='gray')
            ax.set_title(self.name)

        emb = MatplotlibEmbed(parent=parent, figsize=(4, 4))
        emb.create_figure(draw)
        return True
