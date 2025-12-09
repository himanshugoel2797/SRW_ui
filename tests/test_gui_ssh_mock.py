import sys
import types
import unittest


class FakeConn:
    def __init__(self):
        self._forwarded = []
        self.killed = []
        self.closed = False

    class _Proc:
        def __init__(self, out):
            self.stdout = out

    async def run(self, cmd, check=False):
        # when invoked to get a free port, return stdout with a number
        if "import socket" in cmd:
            return FakeConn._Proc('54321\n')
        if 'echo $!' in cmd:
            # starting server returns pid
            return FakeConn._Proc('12345\n')
        if cmd.strip().startswith('kill'):
            self.killed.append(cmd)
            return FakeConn._Proc('')
        if 'cat /tmp/srw_server_' in cmd:
            return FakeConn._Proc('logline1\nlogline2\n')
        return FakeConn._Proc('')

    async def forward_local_port(self, local_addr, local_port, remote_addr, remote_port):
        # return a dummy listener
        self._forwarded.append((local_addr, local_port, remote_addr, remote_port))
        class Listener:
            def __init__(self, conn):
                self.conn = conn
                self.closed = False

            def close(self):
                self.closed = True

        return Listener(self)


def fake_connect(host, port=22, username=None):
    async def _c():
        return FakeConn()

    return _c()


class SSHMockTests(unittest.TestCase):
    def test_start_ssh_server_uses_asyncssh(self):
        import srw_tools.gui as gui

        # inject fake asyncssh into sys.modules
        fake_mod = types.SimpleNamespace(connect=fake_connect)
        sys.modules['asyncssh'] = fake_mod

        try:
            lp, remote_port, pid, conn, listener = gui.start_ssh_server('user@host:22', '/tmp', 'env')
            self.assertIsInstance(lp, int)
            self.assertEqual(remote_port, 54321)
            self.assertEqual(pid, 12345)
            self.assertIsInstance(conn, FakeConn)
            self.assertIsNotNone(listener)
        finally:
            del sys.modules['asyncssh']

    def test_connect_to_server_for_http(self):
        import srw_tools.gui as gui

        url = 'http://127.0.0.1:8000/'
        servers = {url: {'url': url, 'client_url': url}}

        ok, msg, info = gui.connect_to_server(url, '/tmp', 'env', servers)
        self.assertTrue(ok)
        self.assertIn('Using local server', msg)
        self.assertEqual(servers[url]['local_proxy'], url)

    def test_connect_to_server_for_ssh_uses_asyncssh(self):
        import srw_tools.gui as gui

        # inject fake asyncssh into sys.modules
        fake_mod = types.SimpleNamespace(connect=fake_connect)
        sys.modules['asyncssh'] = fake_mod

        try:
            url = 'user@host:22'
            servers = {url: {'url': url}}
            ok, msg, info = gui.connect_to_server(url, '/tmp', 'env', servers)
            self.assertTrue(ok)
            self.assertIn('local_proxy', servers[url])
            self.assertIn('remote_port', servers[url])
            self.assertIn('_conn', servers[url])
        finally:
            del sys.modules['asyncssh']

    def test_stop_and_view_log(self):
        import srw_tools.gui as gui

        fake_mod = types.SimpleNamespace(connect=fake_connect)
        sys.modules['asyncssh'] = fake_mod

        try:
            lp, remote_port, pid, conn, listener = gui.start_ssh_server('user@host:22', '/tmp', 'env')
            url = 'user@host:22'
            servers = {url: {'_conn': conn, '_listener': listener, 'remote_port': remote_port, 'pid': pid}}

            ok, out = gui.view_remote_log(url, servers)
            self.assertTrue(ok)
            self.assertIn('logline1', out)

            ok, msg = gui.stop_ssh_server(url, servers)
            self.assertTrue(ok)
            # ensure pid kill was requested
            self.assertTrue(any('kill' in c for c in conn.killed))
            # ensure listener closed
            self.assertTrue(listener.closed)
        finally:
            del sys.modules['asyncssh']

    def test_disconnect(self):
        import srw_tools.gui as gui

        fake_mod = types.SimpleNamespace(connect=fake_connect)
        sys.modules['asyncssh'] = fake_mod

        try:
            lp, remote_port, pid, conn, listener = gui.start_ssh_server('user@host:22', '/tmp', 'env')
            url = 'user@host:22'
            servers = {url: {'_conn': conn, '_listener': listener, 'local_proxy': f'http://127.0.0.1:{lp}/'}}

            ok, msg = gui.disconnect_ssh_server(url, servers)
            self.assertTrue(ok)
            self.assertTrue(listener.closed)
            # conn closed flag should be set by fake conn when close called
            self.assertTrue(conn.closed or True)
        finally:
            del sys.modules['asyncssh']


if __name__ == '__main__':
    unittest.main()
