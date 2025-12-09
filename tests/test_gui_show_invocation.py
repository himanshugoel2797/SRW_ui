import unittest

from srw_tools.visualizer import register_visualizer, _REGISTRY, Visualizer
from srw_tools.gui import make_visualizer_buttons


class ShowInvocationTests(unittest.TestCase):
    def test_visualizer_show_is_called_when_present(self):
        # create and register a temporary visualizer
        called = {'value': False}

        class TempShowVisualizer(Visualizer):
            name = 'temp_show'

            def local_process(self, data=None):
                # produce some processed data and allow the view() method
                # to decide to attach a UI.
                return {'ok': True}

            def view(self, data=None):
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
            # the GUI launches the view but shouldn't expect processed data
            self.assertIsNone(rv)
        finally:
            _REGISTRY.pop('temp_show', None)
    def test_process_and_view_called(self):
        called = {'process': False, 'view': False, 'data': None}

        class TempPV(Visualizer):
            name = 'temp_pv'

            def local_process(self, data=None):
                called['process'] = True
                return {'a': 1}

            def view(self, data=None):
                called['view'] = True
                # Visualizer should process the params itself (GUI passed
                # only the param dict). Call local_process to produce data.
                output = self.local_process(data)
                called['data'] = output
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
            # view handled presentation; GUI shouldn't return the processed data
            self.assertIsNone(rv)
        finally:
            _REGISTRY.pop('temp_pv', None)


if __name__ == '__main__':
    unittest.main()
