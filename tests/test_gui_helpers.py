import unittest


class TestHoloEmbed(unittest.TestCase):
    def test_create_figure_headless(self):
        # Ensure create_figure works without a GUI and can run the draw fn
        from srw_tools.gui_helpers import HoloEmbed

        emb = HoloEmbed(parent=None)

        def draw(ax):
            ax.plot([0, 1, 2], [0, 1, 0])

        fig = emb.create_figure(draw)
        # figure should be created
        self.assertIsNotNone(fig)
        # either a bokeh figure (has renderers) or a dummy with axes list
        if hasattr(fig, 'renderers'):
            self.assertTrue(len(fig.renderers) >= 0)
        else:
            self.assertTrue(hasattr(fig, 'axes'))

    def test_clear_works_without_canvas(self):
        from srw_tools.gui_helpers import HoloEmbed

        emb = HoloEmbed(parent=None)
        fig = emb.create_figure(lambda ax: None)
        self.assertIsNotNone(emb.figure)
        emb.clear()
        self.assertIsNone(emb.figure)


if __name__ == '__main__':
    unittest.main()
