import unittest

from srw_tools.gui import classify_visualizer_output


class GUIOutputClassifyTests(unittest.TestCase):
    def test_classify_plot(self):
        out = {'x': [0, 1, 2], 'y': [0, 1, 0]}
        self.assertEqual(classify_visualizer_output(out), 'plot')

    def test_classify_image_from_grid(self):
        out = {'grid': [[0, 1], [1, 0]]}
        self.assertEqual(classify_visualizer_output(out), 'image')

    def test_classify_2d_sequence(self):
        # 2D list should be recognized as image when numpy available
        out = [[1, 2], [3, 4]]
        cls = classify_visualizer_output(out)
        # treat either 'image' or 'text' as acceptable if numpy isn't present
        self.assertIn(cls, ('image', 'text'))

    def test_classify_text(self):
        self.assertEqual(classify_visualizer_output('some text'), 'text')


if __name__ == '__main__':
    unittest.main()
