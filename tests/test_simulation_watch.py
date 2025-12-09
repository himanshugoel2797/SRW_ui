import unittest
import tempfile
import os
import time
from pathlib import Path

from srw_tools.simulation_scripts import script_manager


def write_file(p, contents):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(contents)


class SimulationWatchTests(unittest.TestCase):
    def test_watch_detects_changes(self):
        called = {'ok': False, 'data': None}

        with tempfile.TemporaryDirectory() as td:
            # start watching empty dir
            def cb(dct):
                called['ok'] = True
                called['data'] = dct

            script_manager.clear_cache(td)
            script_manager.add_watch(td, cb, interval=0.1)
            try:
                # create a script after some time so watch thread sees it
                time.sleep(0.15)
                p = os.path.join(td, 'sim_watch.py')
                write_file(p, """
def set_optics():
    pass

varParam = [['name','x','Watched']]
""")

                # allow up to 2s for the watcher to fire
                deadline = time.time() + 2.0
                while time.time() < deadline and not called['ok']:
                    time.sleep(0.05)

                self.assertTrue(called['ok'])
                self.assertIn('Watched', called['data'])
            finally:
                script_manager.remove_watch(td)


if __name__ == '__main__':
    unittest.main()
