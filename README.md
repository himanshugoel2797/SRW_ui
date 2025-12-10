# SRW UI tools (lightweight)

This repository implements a small, easy-to-maintain set of utilities for
running and visualizing SRW simulations. The goal is to keep everything
dependency-light and easy to run locally.

Main pieces
- `srw_tools.ssh_helper` — SSH helpers for running commands and background jobs on remote hosts
- `srw_tools.git_helper` — convenient wrappers around git commands
- `srw_tools.visualizer` — base class and registry for visualizer scripts
- `srw_tools/visualizers/` — drop-in directory for your custom visualizers
# SRW UI tools (lightweight)

A small collection of utilities for running and visualizing SRW simulations.
The project aims to be dependency-light and easy to use locally or on remote
machines via SSH.

Main pieces
- `srw_tools.ssh_helper` — SSH helpers for running commands and background jobs on remote hosts
- `srw_tools.git_helper` — convenient wrappers around git commands
- `srw_tools.visualizer` — base class and registry for visualizer scripts
- `srw_tools/visualizers/` — drop-in directory for custom visualizers

Requirements
- Python 3.8+
- Optional: `numpy` and `matplotlib` for example visualizers
- Optional: `asyncssh` for SSH operations (used by the GUI)

Quickstart
- List visualizers:

```bash
python -m srw_tools.cli visualizer list
```

- Run a visualizer from the CLI:

```bash
python -m srw_tools.cli visualizer run --name=sine
```

- Run the Tkinter GUI:

```bash
python -m srw_tools.cli
```

SSH / Remote execution
- The GUI allows connecting to SSH targets (format `user@host[:port]`).
  When connected the GUI stores an active SSH connection which can be used
  to run commands on the remote host.
- Use `srw_tools.ssh_helper` (or the GUI) to run remote commands, start background jobs, and fetch remote files.

If you need to run a remote visualizer process and receive structured output,
configure the server entry with a `remote_cmd` template (used by visualizers).
The template may include `{name}` and `{params}` which will be filled with
visualizer name and a JSON-encoded parameter dictionary.

Example `remote_cmd` value:

```
python -u -c "import json; from srw_tools.visualizer import get_visualizer; params=json.loads('{params}'); print(json.dumps(get_visualizer('{name}')().local_process(params)))"
```

This repository also contains a small native helper in `srw_tools/native/` for
optional C-accelerated routines.
	 - A Matplotlib navigation toolbar is added when a GUI parent window is available,
