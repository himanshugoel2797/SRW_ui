"""Example visualizer placed under the new visualizers package.

It registers a tiny visualizer called 'square' so tests can confirm
auto-loading works.
"""
from ..visualizer import Visualizer, register_visualizer


@register_visualizer
class CoherentModeVisualizer(Visualizer):
    name = 'coherent_mode_viewer'
    group = 'Coherent Modes'

    def local_process(self, data=None):
        # produce a simple numeric grid rather than requiring external deps
        size = (data or {}).get('size', 4)
        grid = [[1 if (i % 2 == 0 and j % 2 == 0) else 0 for j in range(size)] for i in range(size)]
        return {'grid': grid}

    def parameters(self):
        return [
            {'name': 'file', 'type': 'file', 'default': '', 'label': 'File'},
            {'name': 'simulation', 'type': 'simulation', 'default': '', 'label': 'Simulation'},
            {'name': 'break1', 'type': 'newline', 'label': ''},
            {'name': 'Base CM index', 'type': 'int', 'default': 0, 'label': 'Base CM index'},
            {'name': 'break2', 'type': 'newline', 'label': ''},
            {'name': 'Number of CMs', 'type': 'int', 'default': 1, 'label': 'Number of CMs'},
        ]

    def view(self, data=None):
        """Display the grid as an image when running in a GUI, otherwise return data."""
        output = self.process(data)

        # Use the MatplotlibEmbed helper for consistent embedding
        try:
            from ..gui_helpers import MatplotlibEmbed
        except Exception:
            return output

        def draw(ax):
            ax.imshow(output['grid'], cmap='gray')
            ax.set_title(self.name)

        emb = MatplotlibEmbed(figsize=(4, 4))
        emb.create_figure(draw)
        return True
