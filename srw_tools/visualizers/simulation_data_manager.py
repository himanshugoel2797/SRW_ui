"""Simulation Data Manager visualizer

Provides a GUI for managing simulation data directories: list, create, fork,
delete folders, export/import zip archives, and commit backups using git.
"""
from __future__ import annotations

from ..visualizer import Visualizer, register_visualizer
from .. import simulation_scripts
from ..git_helper import stage_files_with_annex, annex_available, commit, _run_git
from ..folder_utils import list_folders, format_folder_display

from pathlib import Path
from typing import Optional, Dict, Any
import shutil
import zipfile
import threading


def _is_git_lfs_available(cwd: Optional[str] = None) -> bool:
    """Check if git-lfs is available in the system."""
    try:
        rc, out, err = _run_git(["lfs", "version"], cwd=cwd)
        return rc == 0
    except Exception:
        return False


@register_visualizer
class SimulationDataManager(Visualizer):
    name = 'simulation_manager'
    group = 'Data'

    def parameters(self):
        return [
            {'name': 'data_root', 'type': 'directory', 'default': str(Path('.').resolve()), 'label': 'Data root'},
            {'name': 'show_hidden', 'type': 'bool', 'default': False, 'label': 'Show hidden folders'},
            {'name': 'scripts_only', 'type': 'bool', 'default': True, 'label': 'Only show folders containing a simulation script'},
        ]

    def local_process(self, data=None):
        root = Path((data or {}).get('data_root') or '.')
        show_hidden = bool((data or {}).get('show_hidden'))
        scripts_only = bool((data or {}).get('scripts_only', True))
        folders = list_folders(root, show_hidden=show_hidden, scripts_only=scripts_only, 
                              script_manager=simulation_scripts)
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
        scripts_only = bool(d.get('scripts_only', True))

        def _refresh_list(lb):
            folders = list_folders(root_dir, show_hidden=show_hidden, scripts_only=scripts_only,
                                  script_manager=simulation_scripts)
            lb.delete(0, 'end')
            for f in folders:
                lb.insert('end', format_folder_display(f))

        def _selected_name(lb):
            sel = lb.curselection()
            if not sel:
                return None
            text = lb.get(sel[0])
            if ' - ' in text:
                return text.split(' - ', 1)[1].split(' (', 1)[0]
            if ' (' in text:
                return text.split(' (', 1)[0]
            return text

        def _ensure_root_exists():
            try:
                root_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror('Error', f'Unable to create data root: {e}')

        win = tk.Toplevel()
        win.title('Simulation Data Manager')
        win.geometry('1000x400')
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

        name_lbl = tk.Label(right, text='Folder name:')
        name_lbl.pack(pady=(4, 0))

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
            try:
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
            try:
                files = [str(p) for p in folder.rglob('*') if p.is_file()]
                if not files:
                    messagebox.showinfo('Backup', 'Nothing to backup')
                    return
                
                rc, out, err = _run_git(["rev-parse", "--show-toplevel"], cwd=str(root_dir))
                workdir = str(root_dir)
                if rc == 0 and out:
                    workdir = out.strip()
                
                ok = stage_files_with_annex(files, path=workdir)
                if not ok:
                    messagebox.showerror('Backup', 'git add failed')
                    return
                
                ok = commit(f'Backup simulation data: {name}', path=workdir)
                if not ok:
                    messagebox.showerror('Backup', 'git commit failed')
                    return
                
                if annex_available(path=workdir):
                    _update_status('Backup committed (annex)')
                elif _is_git_lfs_available(cwd=workdir):
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

        lb.focus_set()
        return True