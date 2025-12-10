import unittest
from types import SimpleNamespace

import srw_tools.gui as gui


class SSHMockTests(unittest.TestCase):
    def test_start_ssh_server_sets_remote_forward_and_registers(self):
        servers = {}
        url = 'user@host'
        path = '/tmp'
        env = 'env'

        # fake callback server returns a known port
        def fake_start_callback_server(srv_map, u):
            return 'cb-id', 'http://127.0.0.1:12345/', None, None

        # capture args passed to start_ssh_server
        captured = {}

        def fake_start_ssh_server(u, p, e, reverse_forward_local_port=None):
            captured['reverse_forward_local_port'] = reverse_forward_local_port
            return (50000, 8000, 42, 'conn', 'listener', 40000, 'remotelistener')

        # monkeypatch functions
        gui.start_callback_server, orig_cb = fake_start_callback_server, gui.start_callback_server
        gui.start_ssh_server, orig_ssh = fake_start_ssh_server, gui.start_ssh_server
        try:
            ok, msg, info = gui.connect_to_server(url, path, env, servers)
            self.assertTrue(ok)
            entry = servers[url]
            # verify callback info captured and transformed
            self.assertEqual(entry['callback_id'], 'cb-id')
            self.assertEqual(entry['callback_url'], 'http://127.0.0.1:12345/')
            self.assertEqual(entry['callback_remote_url'], 'http://127.0.0.1:40000/')
            self.assertEqual(captured['reverse_forward_local_port'], 12345)
        finally:
            gui.start_callback_server = orig_cb
            gui.start_ssh_server = orig_ssh

    def test_disconnect_closes_remote_cb_listener(self):
        servers = {}
        url = 'user@host'
        # create mock listener that tracks close calls
        class MockListener:
            def __init__(self):
                self.closed = False
            def close(self):
                self.closed = True

        servers[url] = {'_conn': SimpleNamespace(close=lambda: None), '_listener': SimpleNamespace(close=lambda: None),
                        '_remote_cb_listener': MockListener(), 'client_url': 'http://127.0.0.1:8000/',
                        'callback_id': 'cb-id', 'callback_url': 'http://127.0.0.1:12345/', 'callback_remote_url': 'http://127.0.0.1:40000/'}
        ok, msg = gui.disconnect_ssh_server(url, servers)
        self.assertTrue(ok)
        self.assertNotIn('_remote_cb_listener', servers[url])
        self.assertNotIn('callback_remote_url', servers[url])



if __name__ == '__main__':
    unittest.main()
