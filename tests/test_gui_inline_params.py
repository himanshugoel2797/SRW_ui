import unittest
import tkinter as tk

from srw_tools.visualizer import register_visualizer, _REGISTRY
from srw_tools.gui import build_frame
from srw_tools.simulation_scripts import script_manager


class InlineParamsTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        try:
            self.root.withdraw()
        except Exception:
            pass

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_inline_params_and_callback_use_values(self):
        # prepare a stable simulation list
        orig = script_manager.list_simulation_scripts

        def fake_sims():
            return {'S1': '/tmp/s1.py', 'S2': '/tmp/s2.py'}

        try:
            # monkeypatch the singleton manager used by GUI
            import srw_tools.gui as g
            g.script_manager.list_simulation_scripts = lambda base_dir=None: fake_sims()

            called = {}

            class InlineVis:
                name = 'inline'

                def __init__(self, config=None):
                    pass

                def parameters(self):
                    return [
                        {'name': 'a', 'type': 'int', 'default': 2, 'label': 'A'},
                        {'name': 'flag', 'type': 'bool', 'default': False, 'label': 'Flag'},
                        {'name': 'newline', 'type': 'newline', 'label': ''},
                        {'name': 'sim', 'type': 'simulation', 'default': 'S1', 'label': 'Sim'},
                        {'name': 'file', 'type': 'file', 'default': '', 'label': 'File'},
                        {'name': 'directory', 'type': 'directory', 'default': '', 'label': 'Directory'}
                    ]

                def process(self, data=None):
                    # return what we got for validation
                    called['data'] = data
                    return data

                def view(self, data=None):
                    # GUI provides raw params; visualizer handles processing
                    return self.process(data)

            register_visualizer(InlineVis)
            try:
                frame = build_frame(self.root)

                # find the row with _vis_name == 'inline'
                def find_row(w):
                    if getattr(w, '_vis_name', None) == 'inline':
                        return w
                    for c in w.winfo_children():
                        r = find_row(c)
                        if r:
                            return r
                    return None

                row = find_row(frame)
                self.assertIsNotNone(row)
                # check parameter widgets exist
                self.assertIn('a', row._param_widgets)
                self.assertIn('flag', row._param_widgets)
                self.assertIn('sim', row._param_widgets)
                # parameter labels should exist next to widgets
                self.assertIn('a', getattr(row, '_param_labels'))
                self.assertIn('flag', getattr(row, '_param_labels'))
                self.assertIn('sim', getattr(row, '_param_labels'))
                self.assertIn('file', getattr(row, '_param_labels'))
                self.assertIn('directory', getattr(row, '_param_labels'))

                # newline should create multiple param rows inside the params area
                self.assertTrue(hasattr(row, '_param_rows'))
                self.assertTrue(len(row._param_rows) >= 2)

                # ensure label 'A' is in the first sub-row and 'Sim' in a later one
                a_label = row._param_labels['a']
                sim_label = row._param_labels['sim']
                self.assertIn(a_label.master, row._param_rows)
                self.assertIn(sim_label.master, row._param_rows)

                # params container should appear before the button in the column
                button = row._button
                col = button.master
                children = list(col.winfo_children())
                # the params_frame (parent of label masters) should come before the button
                params_container = a_label.master.master
                self.assertLess(children.index(params_container), children.index(button))

                # set values
                ent, _ = row._param_widgets['a']
                ent.delete(0, tk.END)
                ent.insert(0, '7')

                var, _ = row._param_widgets['flag']
                var.set(True)

                sval, _ = row._param_widgets['sim']
                sval.set('S2')

                fvar, _ = row._param_widgets['file']
                fvar.set('/tmp/x.txt')

                dvar, _ = row._param_widgets['directory']
                dvar.set('/tmp/some/dir')

                # call callback and ensure values were passed to process
                rv = row._callback()
                self.assertEqual(called['data']['a'], 7)
                self.assertEqual(called['data']['flag'], True)
                self.assertEqual(called['data']['sim'], 'S2')
                # file/dir values come through as strings
                self.assertEqual(called['data']['file'], '/tmp/x.txt')
                self.assertEqual(called['data']['directory'], '/tmp/some/dir')
                # GUI launches the visualizer view; processed data is not
                # returned to the caller in this flow.
                self.assertIsNone(rv)

            finally:
                _REGISTRY.pop('inline', None)
        finally:
            # restore
            import srw_tools.gui as g
            g.script_manager.list_simulation_scripts = orig


if __name__ == '__main__':
    unittest.main()
