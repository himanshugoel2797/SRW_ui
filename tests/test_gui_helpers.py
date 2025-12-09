import unittest


class TestMatplotlibEmbed(unittest.TestCase):
    def test_create_figure_headless(self):
        # Ensure create_figure can create a matplotlib Figure without tkinter
        from srw_tools.gui_helpers import MatplotlibEmbed

        emb = MatplotlibEmbed(parent=None)

        def draw(ax):
            ax.plot([0, 1, 2], [0, 1, 0])

        fig = emb.create_figure(draw)
        # figure should be created and contain at least one axes
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.axes) >= 1)

    def test_clear_works_without_canvas(self):
        from srw_tools.gui_helpers import MatplotlibEmbed

        emb = MatplotlibEmbed(parent=None)
        fig = emb.create_figure()
        self.assertIsNotNone(emb.figure)
        emb.clear()
        self.assertIsNone(emb.figure)


if __name__ == '__main__':
    unittest.main()
