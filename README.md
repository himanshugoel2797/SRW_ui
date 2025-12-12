# SRW UI tools (lightweight)

This repository implements a small, easy-to-maintain set of utilities for
running and visualizing SRW simulations. The goal is to keep everything
dependency-light and easy to run locally.

Main pieces
- `srw_tools.ssh_helper` — SSH helpers for running commands and background jobs on remote hosts
- `srw_tools.git_helper` — convenient wrappers around git commands
  - Now includes optional `git-annex` support for managing large or
    non-code files. New helpers include `annex_available`, `init_annex`,
    `annex_add`, `annex_get`, `annex_drop`, and `stage_files_with_annex`.
    `stage_files_with_annex` will auto-select annex for files by
    extension or size when `git-annex` is available.

  Example:
  ```py
  from srw_tools import git_helper as gh

  # stage files automatically using annex for large binaries when available
  files = ['sim.out', 'params.json']
  ok = gh.stage_files_with_annex(files, path='path/to/repo')
  if ok:
    gh.commit('backup', path='path/to/repo')
  ```
- `srw_tools.visualizer` — base class and registry for visualizer scripts
- `srw_tools/visualizers/` — drop-in directory for your custom visualizers
 - `srw_tools.visualizers/simulation_data_manager` — a visualizer for managing simulation directories. It now by default filters to folders that contain a simulation script (detected via `srw_tools.simulation_scripts` module).
 
CLI
- `srw_tools annex` — git-annex convenience commands available on the CLI (also available as a nested `git annex`). Use:
  - `srw_tools annex available --path <repo>` to check if `git-annex` is available
  - `srw_tools annex init [--name NAME] --path <repo>` to initialize annex in a repo
  - `srw_tools annex add <files...> --path <repo>` to annex files
  Nested commands via `git`:
    - `srw_tools git annex available --path <repo>` to check for `git-annex` availability
    - `srw_tools git annex init [--name NAME] --path <repo>` to initialize annex
    - `srw_tools git annex add <files...> --path <repo>` to add files to annex
    - `srw_tools git annex get <files...> --path <repo>` to fetch annexed files
    - `srw_tools git annex drop <files...> --path <repo>` to drop local annexed content

  JSON output:
    - Use the `--json` flag with annex commands to get JSON responses. Example:
      ```
      $ srw_tools git annex available --path repo --json
      {"available": true}
      ```
  - `srw_tools annex get <files...> --path <repo>` to fetch annexed files
  - `srw_tools annex drop <files...> --path <repo>` to drop local annexed content
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
    - metadata directory (metadata used by this tool)
    - notes.md