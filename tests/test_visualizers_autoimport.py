import unittest
from srw_tools.visualizer import list_visualizers, get_visualizer


class VisualizersAutoImportTests(unittest.TestCase):
    def test_square_visualizer_loaded(self):
        names = list_visualizers()
        self.assertIn('square', names)

    def test_run_square_visualizer(self):
        cls = get_visualizer('square')
        inst = cls()
        out = inst.run({'size': 3})
        self.assertIn('grid', out)


if __name__ == '__main__':
    unittest.main()
