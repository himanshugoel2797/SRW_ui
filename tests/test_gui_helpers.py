import unittest


class TestMatplotlibEmbed(unittest.TestCase):
    def test_create_figure_headless(self):
        # Ensure create_figure works without a GUI and can run the draw fn
        from srw_tools.gui_helpers import MatplotlibEmbed

        emb = MatplotlibEmbed(parent=None)

        def draw(ax):
            ax.plot([0, 1, 2], [0, 1, 0])

        fig = emb.create_figure(draw)
        # figure should be created
        self.assertIsNotNone(fig)
        # either a matplotlib figure or a dummy with axes list
        if hasattr(fig, 'canvas') or hasattr(fig, 'savefig'):
            # matplotlib figures expose savefig or canvas
            self.assertTrue(True)
        else:
            self.assertTrue(hasattr(fig, 'axes'))

    def test_clear_works_without_canvas(self):
        from srw_tools.gui_helpers import MatplotlibEmbed

        emb = MatplotlibEmbed(parent=None)
        fig = emb.create_figure(lambda ax: None)
        self.assertIsNotNone(emb.figure)
        emb.clear()
        self.assertIsNone(emb.figure)

    def test_create_figure_with_parent_creates_toolbar(self):
        from srw_tools.gui_helpers import MatplotlibEmbed
        import tkinter as tk

        root = tk.Tk()
        try:
            root.withdraw()
        except Exception:
            pass

        frame = tk.Frame(root)
        frame.pack()

        emb = MatplotlibEmbed(parent=frame)

        def draw(ax):
            ax.plot([0, 1], [0, 1])

        fig = emb.create_figure(draw)
        # if a canvas was created, toolbar should also be created
        if getattr(emb, 'canvas', None) is not None:
            self.assertIsNotNone(getattr(emb, 'toolbar', None))
        else:
            # headless backends won't create a canvas or toolbar
            self.assertIsNone(getattr(emb, 'toolbar', None))

        emb.clear()
        self.assertIsNone(emb.figure)
        self.assertIsNone(getattr(emb, 'canvas', None))
        self.assertIsNone(getattr(emb, 'toolbar', None))

        try:
            root.destroy()
        except Exception:
            pass


if __name__ == '__main__':
    unittest.main()
