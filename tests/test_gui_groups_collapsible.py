import unittest
import tkinter as tk

from srw_tools.gui import list_visualizers_by_group, build_frame


class GUICollapsibleGroupTests(unittest.TestCase):
    def setUp(self):
        # create a root and keep it hidden to avoid opening windows during tests
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

    def test_group_toggle_hides_and_shows_content(self):
        # Build a frame; it will create group headers and content frames.
        frame = build_frame(self.root)

        # find a group frame with our helper attribute
        groups = list_visualizers_by_group()
        # choose the first group key
        first_group = next(iter(sorted(groups.keys())))

        # locate the corresponding content frame child
        content_frame = None
        for child in frame.winfo_children():
            # groups_container contains header+content pairs; find content by attribute
            for sub in child.winfo_children():
                if getattr(sub, '_group_name', None) == first_group:
                    content_frame = sub
                    break
            if content_frame:
                break

        self.assertIsNotNone(content_frame, 'Could not locate content frame for group')
        btn = getattr(content_frame, '_toggle_button', None)
        self.assertIsNotNone(btn, 'Toggle button not found on group frame')

        # initially the content should be managed (packed)
        self.assertTrue(content_frame.winfo_manager() != '')

        # invoke the toggle to collapse
        btn.invoke()
        self.assertEqual(content_frame.winfo_manager(), '')

        # invoke again to expand
        btn.invoke()
        self.assertTrue(content_frame.winfo_manager() != '')


if __name__ == '__main__':
    unittest.main()
