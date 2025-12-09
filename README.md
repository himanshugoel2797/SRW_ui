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
