import unittest

from srw_tools.visualizer import register_visualizer, _REGISTRY
from srw_tools.gui import make_visualizer_buttons


class ShowInvocationTests(unittest.TestCase):
    def test_visualizer_show_is_called_when_present(self):
        # create and register a temporary visualizer
        called = {'value': False}

        class TempShowVisualizer:
            name = 'temp_show'

            def __init__(self, config=None):
                pass

            def run(self, data=None):
                return {'ok': True}

            def show(self, parent=None, data=None):
                called['value'] = True
                return 'shown'

        # register
        register_visualizer(TempShowVisualizer)

        try:
            created = {}

            def fake_create_button(name, callback):
                created[name] = callback
                return name

            make_visualizer_buttons(fake_create_button)

            # ensure our callback exists and calling it triggers show
            self.assertIn('temp_show', created)
            rv = created['temp_show']()
            self.assertTrue(called['value'])
            self.assertEqual(rv, 'shown')
        finally:
            _REGISTRY.pop('temp_show', None)
    def test_process_and_view_called(self):
        called = {'process': False, 'view': False, 'data': None}

        class TempPV:
            name = 'temp_pv'

            def __init__(self, config=None):
                pass

            def process(self, data=None):
                called['process'] = True
                return {'a': 1}

            def view(self, parent=None, data=None):
                called['view'] = True
                called['data'] = data
                return 'viewed'

        register_visualizer(TempPV)
        try:
            created = {}

            def fake_create_button(name, callback):
                created[name] = callback
                return name

            make_visualizer_buttons(fake_create_button)

            self.assertIn('temp_pv', created)
            rv = created['temp_pv']()
            self.assertTrue(called['process'])
            self.assertTrue(called['view'])
            self.assertEqual(called['data'], {'a': 1})
            self.assertEqual(rv, 'viewed')
        finally:
            _REGISTRY.pop('temp_pv', None)


if __name__ == '__main__':
    unittest.main()
