import unittest
from srw_tools.visualizer import list_visualizers, get_visualizer


class VisualizerTests(unittest.TestCase):
    def test_registry_has_sine(self):
        names = list_visualizers()
        # example visualizer 'sine' should be registered by examples module
        self.assertIn('sine', names)

    def test_get_visualizer(self):
        cls = get_visualizer('sine')
        inst = cls()
        self.assertTrue(hasattr(inst, 'run'))


if __name__ == '__main__':
    unittest.main()
