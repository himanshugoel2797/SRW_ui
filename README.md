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

SSH / Remote execution
- The GUI allows connecting to SSH targets (format `user@host[:port]`).
  When connected the GUI stores an active SSH connection which can be used
  to run commands on the remote host.

This repository also contains a small native helper in `srw_tools/native/` for C-accelerated routines. 

# Simulation Data Structure
- root
  - simulation base directory
    - main python file ("run.py" etc)
    - simulation data directory
    - plot directory (Stores minimum resolution data, and plots of everything, just in-case)
    - notes.md