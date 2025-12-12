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


def annex_available(path: Optional[str] = None) -> bool:
    """Return True if git-annex is available in PATH and usable in `path`."""
    rc, out, err = _run_git(["annex", "version"], cwd=path)
    return rc == 0


def init_annex(path: Optional[str] = None, name: Optional[str] = None) -> bool:
    """Initialize git-annex in the repository at `path`.

    If `name` is provided, it will be passed to `git annex init NAME`.
    Returns True on success.
    """
    if not annex_available(path=path):
        return False
    args = ["annex", "init"]
    if name:
        args.append(name)
    rc, out, err = _run_git(args, cwd=path)
    return rc == 0


def annex_add(files: List[str], path: Optional[str] = None) -> Tuple[bool, str]:
    """Add files to git-annex. Returns (success, output)."""
    if not files:
        return False, 'no files'
    if not annex_available(path=path):
        return False, 'git-annex not available'
    args = ["annex", "add"] + list(files)
    rc, out, err = _run_git(args, cwd=path)
    out_str = out or err
    # ensure changes are staged (annex may update symlinks in work tree)
    if rc == 0:
        rc2, out2, err2 = _run_git(["add"] + list(files), cwd=path)
        if rc2 != 0:
            return False, out2 or err2
    return rc == 0, out_str


def annex_get(files: List[str], path: Optional[str] = None) -> Tuple[bool, str]:
    """Fetch content of annexed files to the local repo. Returns (success, output)."""
    if not files:
        return False, 'no files'
    if not annex_available(path=path):
        return False, 'git-annex not available'
    args = ["annex", "get"] + list(files)
    rc, out, err = _run_git(args, cwd=path)
    out_str = out or err
    return rc == 0, out_str


def annex_drop(files: List[str], path: Optional[str] = None) -> Tuple[bool, str]:
    """Drop local content for annexed files.

    Note: this only removes the local content and leaves the annexed key
    and git history intact.
    """
    if not files:
        return False, 'no files'
    if not annex_available(path=path):
        return False, 'git-annex not available'
    args = ["annex", "drop"] + list(files)
    rc, out, err = _run_git(args, cwd=path)
    out_str = out or err
    return rc == 0, out_str


def stage_files_with_annex(
    files: List[str],
    path: Optional[str] = None,
    use_annex: Optional[bool] = None,
    annex_extensions: Optional[List[str]] = None,
    annex_threshold: int = 5 * 1024 * 1024,
) -> bool:
    """Stage files but use git-annex for non-code/large files when available.

    - If `use_annex` is True, attempt to annex all files.
    - If `use_annex` is False, behave like :func:`stage_files`.
    - If `use_annex` is None (default), auto-detect: if git-annex is
      available, annex files whose extension is in `annex_extensions` or
      whose size >= `annex_threshold`.

    Returns True if staging (and annex add) succeeded.
    """
    if not files:
        return False
    if annex_extensions is None:
        annex_extensions = [
            '.npy', '.npz', '.h5', '.hdf5', '.nc', '.jpg', '.jpeg', '.png',
            '.mp4', '.mov', '.avi', '.tar', '.zip', '.bin', '.out', '.dat',
            '.pkl', '.pickle', '.gz', '.bz2', '.xz', '.7z', '.rar',
        ]

    annex_present = annex_available(path=path)

    # decide per-file
    annex_list: List[str] = []
    git_list: List[str] = []
    for f in files:
        try:
            add_to_annex = False
            if use_annex is True and annex_present:
                add_to_annex = True
            elif use_annex is False:
                add_to_annex = False
            else:
                # auto: annex_present required and either ext or threshold
                if annex_present:
                    _, ext = os.path.splitext(f)
                    if ext.lower() in annex_extensions:
                        add_to_annex = True
                    else:
                        try:
                            if os.path.getsize(f) >= annex_threshold:
                                add_to_annex = True
                        except Exception:
                            # if we can't stat the file, fallback to git
                            add_to_annex = False
            if add_to_annex:
                annex_list.append(f)
            else:
                git_list.append(f)
        except Exception:
            git_list.append(f)

    # perform annex adds first
    if annex_list:
        ok, out = annex_add(annex_list, path=path)
        if not ok:
            return False

    # stage remaining files with git add (also ensures annex symlinks are staged)
    if git_list:
        rc, out, err = _run_git(["add"] + git_list, cwd=path)
        if rc != 0:
            return False
    return True


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

