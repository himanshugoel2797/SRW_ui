import io
import sys
import unittest

import srw_tools.cli as st


class CLITests(unittest.TestCase):
    def test_visualizer_list(self):
        old = sys.stdout
        try:
            sys.stdout = io.StringIO()
            rc = st.main(['visualizer', 'list'])
            out = sys.stdout.getvalue()
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0)
        self.assertIn('sine', out)


if __name__ == '__main__':
    unittest.main()
