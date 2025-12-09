import unittest
import tempfile
import os
from pathlib import Path

from srw_tools.simulation_scripts import script_manager, SimulationScriptManager


def write_file(p, contents):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(contents)


class SimulationDiscoveryTests(unittest.TestCase):
    def test_discovers_scripts_with_set_optics_and_varParam(self):
        with tempfile.TemporaryDirectory() as td:
            # create a file with set_optics and varParam containing ['name',..., 'My Script']
            p1 = os.path.join(td, 'sim1.py')
            write_file(p1, """
def set_optics():
    pass

varParam = [
    ['name', 'description', 'My Script'],
    ['a', 'b', 1]
]
""")

            # nested file should also be found
            nested = os.path.join(td, 'sub', 'nested_sim.py')
            write_file(nested, """
def set_optics():
    pass

varParam = [
    ['x', 'desc', 1],
    ['name', 'label', 'OtherScript']
]
""")

            # Use the singleton manager directly
            results = script_manager.list_simulation_scripts(td, use_cache=False)
            self.assertIsInstance(script_manager, SimulationScriptManager)
            self.assertIn('My Script', results)
            self.assertIn('OtherScript', results)
            self.assertTrue(results['My Script'].endswith('sim1.py'))
            self.assertTrue('nested_sim.py' in results['OtherScript'])

    def test_ignores_files_without_set_optics(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'not_sim.py')
            write_file(p, """
# no set_optics here
varParam = [['name','x','Ignored']]
""")
            results = script_manager.list_simulation_scripts(td, use_cache=False)
            self.assertEqual(results, {})

    def test_handles_non_string_third_values(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'sim2.py')
            write_file(p, """
def set_optics():
    pass

varParam = [['name', 'x', 42]]
""")
            results = script_manager.list_simulation_scripts(td, use_cache=False)
            # third element is int -> should be found as stringified key '42'
            self.assertIn('42', results)


if __name__ == '__main__':
    unittest.main()
