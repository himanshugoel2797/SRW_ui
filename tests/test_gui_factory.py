import unittest


class GUIFactoryTests(unittest.TestCase):
    def test_make_visualizer_buttons_calls_factory_for_each_visualizer(self):
        called = []

        def fake_create_button(name, callback):
            # store name and a stringified return of calling callback
            called.append((name, callable(callback)))
            return name

        # avoid importing tkinter; ensure factory function handles all registered
        # visualizers (there should be at least 'sine' and 'square')
        from srw_tools.gui import make_visualizer_buttons

        created = make_visualizer_buttons(fake_create_button)
        # expect at least two visualizers are present (sine from examples,
        # square from visualizers directory). We don't hard-fail if more.
        # factory returned values for each created button (we returned the name)
        names = list(created)
        self.assertIn('sine', names)
        self.assertIn('square', names)
        # validate that factory was called and callbacks are callable
        self.assertTrue(all(isinstance(cb_ok, bool) and cb_ok for _, cb_ok in called))


if __name__ == '__main__':
    unittest.main()
