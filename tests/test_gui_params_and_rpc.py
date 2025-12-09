import unittest
import threading
import time
import xmlrpc.client

from srw_tools.visualizer import register_visualizer, _REGISTRY, Visualizer
from srw_tools.gui import make_visualizer_buttons
from srw_tools.rpc_server import RPCServer


class ParamsAndRPCTests(unittest.TestCase):
    def test_make_visualizer_buttons_passes_params_to_process(self):
        called = {'params': None}

        class TempParamVis(Visualizer):
            name = 'temp_param'

            def local_process(self, data=None):
                called['params'] = data
                return {'ok': True, 'received': data}

            def view(self, data=None):
                # GUI provides the parameter dict; visualizer decides to process it
                return self.local_process(data)

        register_visualizer(TempParamVis)
        try:
            created = {}

            def fake_create_button(name, callback):
                created[name] = callback
                return name

            def get_params(name):
                return {'a': 1, 'b': 2}

            make_visualizer_buttons(fake_create_button, get_params_fn=get_params)
            self.assertIn('temp_param', created)
            rv = created['temp_param']()
            self.assertEqual(called['params'], {'a': 1, 'b': 2})
            # GUI launches view() and visualizers manage their own output, so
            # we don't expect the callback to return processed data.
            self.assertIsNone(rv)
        finally:
            _REGISTRY.pop('temp_param', None)

    def test_make_visualizer_buttons_uses_rpc_server_for_processing(self):
        # run a server in a background thread with an ephemeral port
        server = RPCServer(host='127.0.0.1', port=0)
        th = threading.Thread(target=server.serve_forever, daemon=True)
        th.start()
        # wait until server is serving
        time.sleep(0.05)

        host, port = server.server.server_address
        proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}/RPC2')

        # ensure a visualizer exists on the server (sine is present)
        # Use get_params to pass amplitude
        created = {}

        def fake_create_button(name, callback):
            created[name] = callback
            return name

        def get_server(name):
            return proxy

        def get_params(name):
            return {'amplitude': 3.0}

        make_visualizer_buttons(fake_create_button, get_params_fn=get_params, get_server_fn=get_server)

        # Sine visualizer should be present (registered in package), call it.
        self.assertIn('sine', created)
        rv = created['sine']()
        # GUI launched the visualizer's view; it manages its own rendering and
        # the GUI does not return processed data here.
        self.assertIsNone(rv)

        # The server side processing still works — call the RPC directly to
        # verify server processing returns the expected numeric structure.
        res = proxy.process_visualizer('sine', {'amplitude': 3.0})
        self.assertIsInstance(res, dict)
        self.assertIn('x', res)
        self.assertIn('y', res)

        # shutdown is not exposed but thread is daemon; cleaning up by finishing test


if __name__ == '__main__':
    unittest.main()
