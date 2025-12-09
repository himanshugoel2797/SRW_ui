import unittest

from srw_tools.visualizer import Visualizer, register_visualizer, _REGISTRY


class DisplayNameTests(unittest.TestCase):
    def test_default_display_name_titleizes_name(self):
        class TempVis(Visualizer):
            name = 'temp_vis'

        v = TempVis()
        self.assertEqual(v.get_display_name(), 'Temp Vis')

    def test_explicit_display_name_used(self):
        class PrettyVis(Visualizer):
            name = 'pretty'
            display_name = 'Pretty Visual'

        v = PrettyVis()
        self.assertEqual(v.get_display_name(), 'Pretty Visual')

    def test_registry_entry_unchanged(self):
        # register a visualizer with a display name and ensure registry
        # key remains the canonical `name` (not display_name)
        class RegVis(Visualizer):
            name = 'reg_vis'
            display_name = 'Registered Visual'

        register_visualizer(RegVis)
        try:
            self.assertIn('reg_vis', _REGISTRY)
            self.assertIs(_REGISTRY['reg_vis'], RegVis)
        finally:
            _REGISTRY.pop('reg_vis', None)


if __name__ == '__main__':
    unittest.main()
