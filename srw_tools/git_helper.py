"""Small git helper utilities without external dependencies.

This keeps a tiny wrapper around common git operations used for
simulation versioning. It uses subprocess to call git and returns
concise structured results.
"""
import subprocess
import os
from typing import Optional, Tuple, List


def _run_git(args: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(["git"] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return -1, '', 'git not found'


def current_commit(path: Optional[str] = None) -> Optional[str]:
    """Return the current commit hash (short) for a repository."""
    rc, out, err = _run_git(["rev-parse", "--short", "HEAD"], cwd=path)
    if rc == 0:
        return out
    return None


def show_status(path: Optional[str] = None) -> str:
    rc, out, err = _run_git(["status", "--porcelain=1"], cwd=path)
    if rc == 0:
        return out
    return err


def tag_simulation(tag: str, message: str = '', path: Optional[str] = None) -> bool:
    args = ["tag", "-a", tag, "-m", message or tag]
    rc, out, err = _run_git(args, cwd=path)
    return rc == 0


def list_tags(path: Optional[str] = None) -> List[str]:
    rc, out, err = _run_git(["tag", "--list"], cwd=path)
    if rc == 0 and out:
        return out.splitlines()
    return []


def stage_files(files: List[str], path: Optional[str] = None) -> bool:
    """Stage the provided files (paths relative to repo root or absolute).

    Returns True on success.
    """
    if not files:
        return False
    args = ["add"] + list(files)
    rc, out, err = _run_git(args, cwd=path)
    return rc == 0


def commit(message: str, path: Optional[str] = None, author: Optional[str] = None) -> bool:
    """Make a commit with the given message. Optionally set author ("Name <email>").

    Returns True if commit succeeded.
    """
    args = ["commit", "-m", message]
    if author:
        args += ["--author", author]
    rc, out, err = _run_git(args, cwd=path)
    return rc == 0


def push(remote: str = 'origin', branch: str = 'main', path: Optional[str] = None, set_upstream: bool = False) -> Tuple[bool, str]:
    """Push the given branch to the named remote. Returns (success, output)."""
    args = ["push"]
    if set_upstream:
        args += ["-u", remote, branch]
    else:
        args += [remote, branch]
    rc, out, err = _run_git(args, cwd=path)
    out_str = out or err
    return rc == 0, out_str


def pull(remote: str = 'origin', branch: str = 'main', path: Optional[str] = None) -> Tuple[bool, str]:
    """Pull updates for the specified remote/branch into the current repo."""
    args = ["pull", remote, branch]
    rc, out, err = _run_git(args, cwd=path)
    out_str = out or err
    return rc == 0, out_str

