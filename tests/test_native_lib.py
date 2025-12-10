import unittest
import importlib
import numpy as np

# Check whether the native shared library is available via srw_tools.nativelib
HAVE_NATIVE = True
try:
    from srw_tools import nativelib as _nativelib
    _nativelib.load_lib()
except Exception:
    HAVE_NATIVE = False


@unittest.skipUnless(HAVE_NATIVE, "srwfast native extension not built; skipping native tests")
class TestNativeLib(unittest.TestCase):
    def test_sum_and_scale_behaviour(self):
        from srw_tools import nativelib
        arr = np.array([1.0, 2.0, 3.0, 4.0])
        s = nativelib.sum_array(arr)
        self.assertAlmostEqual(s, 10.0)

        scaled = nativelib.scale_array(arr, 2.5)
        # scaled should be in-place transformed or returned; check values
        self.assertTrue(np.allclose(scaled, np.array([2.5, 5.0, 7.5, 10.0])))

    def test_python_list_input(self):
        from srw_tools import nativelib
        lst = [0.5, 1.5, 2.5]
        s = nativelib.sum_array(lst)
        self.assertAlmostEqual(s, 4.5)
        scaled = nativelib.scale_array(lst, 2.0)
        self.assertTrue(np.allclose(scaled, np.array([1.0, 3.0, 5.0])))

    def test_file_load(self):
        from srw_tools import nativelib
        import tempfile
        import os
        content = """# header line 1\n# header line 2\n1.0 2.0 3.0\n4.0\n"""
        tf = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf8')
        try:
            tf.write(content)
            tf.flush()
            tf.close()
            headers, values = nativelib.load_file(tf.name)
            self.assertEqual(headers, ['header line 1', 'header line 2'])
            self.assertTrue(np.allclose(values, np.array([1.0, 2.0, 3.0, 4.0])))
        finally:
            os.unlink(tf.name)


if __name__ == '__main__':
    unittest.main()
