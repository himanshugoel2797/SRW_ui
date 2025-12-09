How to debug the GUI in VS Code
--------------------------------

Use the following launch configurations (open the Run view in VS Code):

- "Python: Run SRW GUI (module)"
  - Runs the GUI via `python -m srw_tools.gui` so the `__main__` branch in
    `srw_tools/gui.py` launches the app. This is the simplest way to debug
    the Tkinter-based GUI and step through event handlers.

- "Python: Run SRW CLI (start GUI)"
  - Runs the CLI module (`srw_tools.cli`) which also exposes the GUI entry
    point. Use this when you want to debug any CLI wiring or integration
    before the GUI starts.

Tips
----
- Use the Integrated Terminal for the debug session (configured in launch.json)
  so the GUI can display and accept input.
- Set breakpoints in `srw_tools/gui.py` or any visualizer under
  `srw_tools/visualizers/` to inspect runtime behavior.

If you'd like I can add a third debug config that runs the GUI with an
embedded test server running (useful for quickly exercising remote processing).
