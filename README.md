# SRW UI tools (lightweight)

This repository implements a small, easy-to-maintain set of utilities for
running and visualizing SRW simulations. The goal is to keep everything
dependency-light and easy to run locally.

 Main pieces
 - srw_tools.rpc_server — a tiny XML-RPC server exposing a few helpers
 - srw_tools.git_helper — convenient wrappers around git commands. New convenience functions exist to stage files, make commits, and push/pull to a named remote and branch.
 - srw_tools.visualizer — base class and registry for visualizer scripts
 - srw_tools/visualizers/ — drop-in directory for your custom visualizers; any .py file placed here will be auto-imported and can register itself with the system

 Examples (python):

 ```py
 from srw_tools import git_helper

 # stage files and commit
 git_helper.stage_files(['sim.out', 'params.json'], path='/path/to/repo')
 git_helper.commit('record simulation', path='/path/to/repo')

 # push to origin/main
 git_helper.push(remote='origin', branch='main', path='/path/to/repo', set_upstream=True)

 # pull updates
 git_helper.pull(remote='origin', branch='main', path='/path/to/repo')
 ```
- srw_cli.py — small CLI entrypoint

Requirements
- Python 3.8+
- Optional: numpy and matplotlib for the example visualizer

Dependencies
 - Install the common scientific dependencies used by the visualizers and SRW workflows with:

```bash
pip install -r requirements.txt
```

Note: `srwpy` is listed as a dependency in `requirements.txt` to support SRW-native helpers. Pin exact versions in the requirements file if you need reproducible environments.

Quickstart
 - List visualizers:

```bash
python -m srw_tools.cli visualizer list
```

 - Run the example visualizer (returns OK if a plot was produced):

```bash
python -m srw_tools.cli visualizer run --name=sine
```

 - Start RPC server (file access is not restricted by default):

```bash
python -m srw_tools.cli start-rpc --host 127.0.0.1 --port 8000
```

To restrict file access to a specific folder, pass --dir:

```bash
python -m srw_tools.cli start-rpc --host 127.0.0.1 --port 8000 --dir path/to/allowed/folder
```

GUI
 - Run the Tkinter-based GUI which shows a button for every registered visualizer:

```bash
python -m srw_tools.cli
```
or, if installed via the package entry point (srw-cli), run:

```bash
srw-cli
```

Richer GUI output
 - The GUI now renders visualizer outputs more helpfully: when a visualizer
	 returns numeric data with 'x' and 'y' keys, the GUI will show an embedded
	 matplotlib plot (if matplotlib is installed). When a visualizer returns a
	 2D numeric grid (key 'grid' or a 2D list/array) the GUI displays it with
	 imshow. Other outputs are shown in a small text viewer.

Parameters & remote processing
 - Visualizers can expose a `parameters()` schema — the GUI will prompt you
	 for parameter values before running a visualizer. Parameters are simple
	 typed fields: int, float, str, or bool.
 - The GUI also allows registering RPC servers (XML-RPC). When a server
	 is selected the visualizer's `process()` call will be performed on the
	 remote server (via `process_visualizer(name, params)`), and the result
	 will be handed to `view()` for display locally. This makes it easy to
	 present data produced remotely without reimplementing UI code.
