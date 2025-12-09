import unittest

from srw_tools.visualizer import Visualizer


class VisualizerParametersTests(unittest.TestCase):
    def test_base_visualizer_parameters_defaults_to_empty_list(self):
        v = Visualizer()
        self.assertEqual(v.parameters(), [])


if __name__ == '__main__':
    unittest.main()
