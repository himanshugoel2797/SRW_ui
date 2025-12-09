import unittest

from srw_tools.visualizer import Visualizer, register_visualizer, _REGISTRY
from srw_tools.gui import list_visualizers_by_group


class VisualizerGroupTests(unittest.TestCase):
    def test_default_group_is_other(self):
        class NoGroupVis(Visualizer):
            name = 'nogroup_vis'

        register_visualizer(NoGroupVis)
        try:
            groups = list_visualizers_by_group()
            # ensure the visualizer appears under 'Other'
            self.assertIn('Other', groups)
            self.assertIn('nogroup_vis', groups['Other'])
        finally:
            _REGISTRY.pop('nogroup_vis', None)

    def test_custom_grouping(self):
        class AlphaVis(Visualizer):
            name = 'alpha'
            group = 'Math'

        class BetaVis(Visualizer):
            name = 'beta'
            group = 'Math'

        class ImageVis(Visualizer):
            name = 'imv'
            group = 'Images'

        register_visualizer(AlphaVis)
        register_visualizer(BetaVis)
        register_visualizer(ImageVis)
        try:
            groups = list_visualizers_by_group()
            self.assertIn('Math', groups)
            self.assertIn('Images', groups)
            self.assertIn('alpha', groups['Math'])
            self.assertIn('beta', groups['Math'])
            self.assertIn('imv', groups['Images'])
        finally:
            _REGISTRY.pop('alpha', None)
            _REGISTRY.pop('beta', None)
            _REGISTRY.pop('imv', None)


if __name__ == '__main__':
    unittest.main()
