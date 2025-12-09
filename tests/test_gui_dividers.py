import unittest
import tkinter as tk

from srw_tools.gui import build_frame


class GUIDividerTests(unittest.TestCase):
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

    def test_dividers_present_between_rows_and_groups(self):
        frame = build_frame(self.root)

        found_row_divider = False
        found_group_divider = False

        # walk all widgets and look for markers set by the GUI
        def walk(w):
            nonlocal found_row_divider, found_group_divider
            if getattr(w, '_is_divider', False):
                found_row_divider = True
            if getattr(w, '_is_group_divider', False):
                found_group_divider = True
            for c in w.winfo_children():
                walk(c)

        walk(frame)

        self.assertTrue(found_row_divider, 'No row divider found in UI')
        self.assertTrue(found_group_divider, 'No group divider found in UI')


if __name__ == '__main__':
    unittest.main()
