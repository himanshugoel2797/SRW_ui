import tempfile
import unittest
from srw_tools.rpc_server import RPCServer


class RPCServerTests(unittest.TestCase):
    def test_allowed_paths(self):
        with tempfile.TemporaryDirectory() as td:
            s = RPCServer(allowed_dirs=[td])
            # allowed
            self.assertTrue(s._is_allowed_path(td))
            # not allowed for outside path
            self.assertFalse(s._is_allowed_path('/'))

    def test_file_write_and_read(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            s = RPCServer(allowed_dirs=[td])
            p = os.path.join(td, 'hello.txt')
            self.assertTrue(s.write_file(p, 'hello world'))
            txt = s.read_file(p)
            self.assertEqual(txt, 'hello world')

    def test_execute_command(self):
        s = RPCServer()
        code, out, err = s.execute_command('echo hi')
        self.assertEqual(code, 0)
        self.assertIn('hi', out)


if __name__ == '__main__':
    unittest.main()
