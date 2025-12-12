"""Folder management utilities for simulation data.

Provides reusable functions for listing, creating, copying, and managing
folders containing simulation data. These utilities can be used by
visualizers and other tools.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional


def list_folders(root: Path, show_hidden: bool = False, scripts_only: bool = True, 
                 script_manager=None) -> List[Dict[str, Any]]:
    """List folders under root with metadata.

    Args:
        root: Root directory to scan
        show_hidden: Include folders starting with '.'
        scripts_only: Only include folders containing simulation scripts
        script_manager: Optional script manager instance for discovering scripts

    Returns:
        List of dicts with keys: name, path, size, scripts
    """
    out = []
    if not root.exists() or not root.is_dir():
        return out

    scripts_map = {}
    if scripts_only and script_manager:
        try:
            scripts_map = script_manager.list_simulation_scripts(
                base_dir=str(root), use_cache=True, key_by='path'
            )
        except Exception:
            scripts_map = {}

    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        if not show_hidden and p.name.startswith('.'):
            continue

        size = sum(f.stat().st_size for f in p.rglob('*') if f.is_file() 
                   if not _stat_error(f))

        scripts_in_folder = []
        if scripts_map:
            for spath, sname in scripts_map.items():
                try:
                    if Path(spath).resolve().relative_to(p.resolve()):
                        scripts_in_folder.append(sname)
                except Exception:
                    pass

        if scripts_only and not scripts_in_folder:
            continue

        out.append({
            'name': p.name,
            'path': str(p.resolve()),
            'size': size,
            'scripts': scripts_in_folder,
        })

    return out


def _stat_error(f: Path) -> bool:
    """Helper to check if file stat will fail."""
    try:
        f.stat()
        return False
    except Exception:
        return True


def calculate_folder_size(folder: Path) -> int:
    """Calculate total size of all files in folder tree."""
    size = 0
    for f in folder.rglob('*'):
        if f.is_file() and not _stat_error(f):
            size += f.stat().st_size
    return size


def format_folder_display(folder_info: Dict[str, Any]) -> str:
    """Format folder information for display in UI lists.

    Args:
        folder_info: Dict with keys: name, size, scripts

    Returns:
        Formatted string suitable for display
    """
    size_mb = folder_info['size'] / (1024 * 1024)
    scripts = folder_info.get('scripts') or []
    
    if scripts:
        if len(scripts) > 2:
            script_text = ', '.join(scripts[:2]) + f' (+{len(scripts)-2} more)'
        else:
            script_text = ', '.join(scripts)
        return f"{script_text} - {folder_info['name']} ({size_mb:.2f} MB)"
    else:
        return f"{folder_info['name']} ({size_mb:.2f} MB)"
