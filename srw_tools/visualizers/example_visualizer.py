"""Example visualizer placed under the new visualizers package.

It registers a tiny visualizer called 'square' so tests can confirm
auto-loading works.
"""
from ..visualizer import Visualizer, register_visualizer


@register_visualizer
class SquareVisualizer(Visualizer):
    name = 'square'

    def run(self, data=None):
        # produce a simple numeric grid rather than requiring external deps
        size = (data or {}).get('size', 4)
        grid = [[1 if (i % 2 == 0 and j % 2 == 0) else 0 for j in range(size)] for i in range(size)]
        return {'grid': grid}
