"""Simulation Data Manager visualizer

Provides a small GUI for managing simulation data directories under a
configured root: list available folders, create new folders, fork
existing ones, delete folders, export/import zip archives, and commit
backups using git. The visualizer falls back to returning structured
data when tkinter is not available (so tests and headless usage work).
"""
from __future__ import annotations

from ..visualizer import Visualizer, register_visualizer
from ..simulation_scripts import script_manager
from ..git_helper import stage_files, commit, _run_git

from pathlib import Path
from typing import Optional, Dict, Any, List
import os
import shutil
import zipfile
import subprocess
import threading


def _is_git_lfs_available(cwd: Optional[str] = None) -> bool:
    try:
        # Prefer the helper's _run_git to keep behavior consistent with the
        # rest of the project; it returns rc, out, err.
        rc, out, err = _run_git(["lfs", "version"], cwd=cwd)
        return rc == 0
    except Exception:
        return False


def _list_folders(root: Path, show_hidden: bool = False) -> List[Dict[str, Any]]:
    out = []
    if not root.exists() or not root.is_dir():
        return out
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        if not show_hidden and p.name.startswith('.'):
            continue
        size = 0
        for f in p.rglob('*'):
            try:
                if f.is_file():
                    size += f.stat().st_size
            except Exception:
                pass
        out.append({
            'name': p.name,
            'path': str(p.resolve()),
            'size': size,
        })
    return out


@register_visualizer
class SimulationDataManager(Visualizer):
    name = 'simulation_manager'
    group = 'Data'

    def parameters(self):
        return [
            {'name': 'data_root', 'type': 'directory', 'default': str(Path('.').resolve()), 'label': 'Data root'},
            {'name': 'show_hidden', 'type': 'bool', 'default': False, 'label': 'Show hidden folders'},
        ]

    def local_process(self, data=None):
        root = Path((data or {}).get('data_root') or '.')
        show_hidden = bool((data or {}).get('show_hidden'))
        folders = _list_folders(root, show_hidden=show_hidden)
        return {'folders': folders}

    def view(self, data=None):
        # Use the GUI to display and manage folders; otherwise return data
        try:
            import tkinter as tk
            from tkinter import messagebox, filedialog
        except Exception:
            return self.local_process(data)

        d = data or {}
        root_dir = Path(d.get('data_root') or '.')
        show_hidden = bool(d.get('show_hidden'))

        def _refresh_list(lb):
            folders = _list_folders(root_dir, show_hidden=show_hidden)
            lb.delete(0, 'end')
            for f in folders:
                size_mb = f['size'] / (1024 * 1024)
                lb.insert('end', f"{f['name']} ({size_mb:.2f} MB)")

        def _selected_name(lb):
            sel = lb.curselection()
            if not sel:
                return None
            text = lb.get(sel[0])
            # get name part before space
            return text.split(' ')[0]

        def _ensure_root_exists():
            try:
                root_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror('Error', f'Unable to create data root: {e}')

        win = tk.Toplevel()
        win.title('Simulation Data Manager')
        frame = tk.Frame(win)
        frame.pack(fill='both', expand=True)

        left = tk.Frame(frame)
        left.pack(side='left', fill='both', expand=True, padx=6, pady=6)

        lb = tk.Listbox(left, height=20)
        lb.pack(fill='both', expand=True)
        _ensure_root_exists()
        _refresh_list(lb)

        right = tk.Frame(frame)
        right.pack(side='left', fill='y', padx=6, pady=6)

        name_entry = tk.Entry(right, width=30)
        name_entry.pack(padx=4, pady=(0, 8))
        name_entry.insert(0, '')

        status = tk.Label(right, text='Ready')
        status.pack(pady=(4, 8))

        def _update_status(msg: str):
            try:
                status.config(text=msg)
            except Exception:
                pass

        def _create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning('Create', 'Please provide a folder name')
                return
            dest = root_dir / name
            if dest.exists():
                messagebox.showwarning('Create', f'Folder {name} already exists')
                return
            try:
                dest.mkdir(parents=True)
                _update_status(f'Created {name}')
                _refresh_list(lb)
            except Exception as e:
                messagebox.showerror('Create error', str(e))

        def _delete():
            name = _selected_name(lb)
            if not name:
                messagebox.showwarning('Delete', 'Nothing selected')
                return
            if not messagebox.askyesno('Confirm delete', f'Delete folder {name}?'):
                return
            try:
                shutil.rmtree(root_dir / name)
                _update_status(f'Deleted {name}')
                _refresh_list(lb)
            except Exception as e:
                messagebox.showerror('Delete error', str(e))

        def _fork():
            name = _selected_name(lb)
            if not name:
                messagebox.showwarning('Fork', 'Nothing selected')
                return
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning('Fork', 'Please enter a new name')
                return
            src = root_dir / name
            dst = root_dir / new_name
            if dst.exists():
                messagebox.showwarning('Fork', f'Destination {new_name} already exists')
                return
            def _do_copy():
                try:
                    shutil.copytree(src, dst)
                    _update_status(f'Forked {name} -> {new_name}')
                    _refresh_list(lb)
                except Exception as e:
                    messagebox.showerror('Fork error', str(e))

            threading.Thread(target=_do_copy, daemon=True).start()

        def _export():
            name = _selected_name(lb)
            if not name:
                messagebox.showwarning('Export', 'Nothing selected')
                return
            dst = filedialog.asksaveasfilename(defaultextension='.zip', initialfile=f"{name}.zip")
            if not dst:
                return
            base = root_dir / name
            try:
                # create zip of the folder
                shutil.make_archive(dst[:-4], 'zip', root_dir / name)
                _update_status(f'Exported {name} -> {dst}')
            except Exception as e:
                messagebox.showerror('Export error', str(e))

        def _import():
            src = filedialog.askopenfilename(filetypes=[('Zip files', '*.zip')])
            if not src:
                return
            default_name = Path(src).stem
            if messagebox.askyesno('Import', f'Use folder name {default_name}?'):
                dest_name = default_name
            else:
                dest_name = name_entry.get().strip() or default_name
            dest = root_dir / dest_name
            if dest.exists():
                messagebox.showwarning('Import', f'Destination {dest_name} already exists')
                return
            try:
                with zipfile.ZipFile(src, 'r') as zf:
                    zf.extractall(dest)
                _update_status(f'Imported {src} -> {dest_name}')
                _refresh_list(lb)
            except Exception as e:
                messagebox.showerror('Import error', str(e))

        def _refresh():
            nonlocal root_dir, show_hidden
            # allow on-the-fly changes to data_root via name_entry if provided
            entered_root = name_entry.get().strip()
            if entered_root and Path(entered_root).exists():
                root_dir = Path(entered_root).resolve()
            _refresh_list(lb)

        def _backup():
            name = _selected_name(lb)
            if not name:
                messagebox.showwarning('Backup', 'Nothing selected')
                return
            folder = root_dir / name
            # Stage all files under folder and commit
            try:
                files = [str(p) for p in folder.rglob('*') if p.is_file()]
                if not files:
                    messagebox.showinfo('Backup', 'Nothing to backup')
                    return
                # use the repository root as working directory
                rc, out, err = _run_git(["rev-parse", "--show-toplevel"], cwd=str(root_dir))
                workdir = str(root_dir)
                if rc == 0 and out:
                    workdir = out.strip()
                ok = stage_files(files, path=workdir)
                if not ok:
                    messagebox.showerror('Backup', 'git add failed')
                    return
                ok = commit(f'Backup simulation data: {name}', path=workdir)
                if not ok:
                    messagebox.showerror('Backup', 'git commit failed')
                    return
                # if git-lfs is available, we can add a note to the status
                if _is_git_lfs_available(cwd=workdir):
                    _update_status('Backup committed (LFS)')
                else:
                    _update_status('Backup committed')
            except Exception as e:
                messagebox.showerror('Backup error', str(e))

        btn_create = tk.Button(right, text='Create', width=18, command=_create)
        btn_create.pack(pady=(2, 2))
        btn_fork = tk.Button(right, text='Fork', width=18, command=_fork)
        btn_fork.pack(pady=(2, 2))
        btn_delete = tk.Button(right, text='Delete', width=18, command=_delete)
        btn_delete.pack(pady=(2, 2))
        btn_export = tk.Button(right, text='Export (.zip)', width=18, command=_export)
        btn_export.pack(pady=(2, 2))
        btn_import = tk.Button(right, text='Import (.zip)', width=18, command=_import)
        btn_import.pack(pady=(2, 2))
        btn_refresh = tk.Button(right, text='Refresh', width=18, command=_refresh)
        btn_refresh.pack(pady=(2, 2))
        btn_backup = tk.Button(right, text='Backup (git)', width=18, command=_backup)
        btn_backup.pack(pady=(2, 2))

        # Initially, set focus to listbox
        lb.focus_set()

        return True
# Simulation Data Manager
# Allows for creating/deleting simulation data folders and managing their contents.
# Simulations can be forked, freshly created, or deleted.
# Changes are tracked and backed up via git
# If Git LFS is available, large files are stored via LFS, else only files up to the configured size are stored.
# All scripts can be exported/imported as .zip files for easy sharing.
# A refresh button allows reloading the simulation list from disk.