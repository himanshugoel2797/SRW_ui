"""Simple synchronous SSH helper built on top of asyncssh.

Provides a minimal synchronous wrapper useful for GUI workflows that
need to run commands or start background jobs on remote hosts via SSH.

This keeps asyncssh usage in one place and exposes easy-to-call
blocking helpers for the rest of the codebase.
"""
from typing import Optional, Tuple
import asyncio


class SSHError(RuntimeError):
    pass


def _parse_url(url: str) -> Tuple[Optional[str], str, int]:
    user = None
    host = url
    port = 22
    if '@' in url:
        user, host = url.split('@', 1)
    if ':' in host:
        h, p = host.rsplit(':', 1)
        host = h
        try:
            port = int(p)
        except Exception:
            port = 22
    return user, host, port


def connect_sync(url: str, username: Optional[str] = None, **connect_kwargs):
    """Connect to an SSH host synchronously and return an asyncssh connection object.

    Requires `asyncssh` to be available. This function will raise a clear
    `SSHError` if the library is missing or the connection fails.
    """
    try:
        import asyncssh
    except Exception as e:
        raise SSHError('asyncssh is required for SSH operations') from e

    user, host, port = _parse_url(url)
    if username is None and user:
        username = user

    async def _do_connect():
        conn_params = {'host': host, 'port': port}
        if username:
            conn_params['username'] = username
        conn_params.update(connect_kwargs)
        conn = await asyncssh.connect(**conn_params)
        return conn

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_do_connect())
    finally:
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass


def run_command(conn, cmd: str, check: bool = True, timeout: Optional[float] = None):
    """Run a command on an existing asyncssh connection synchronously.

    Returns a tuple (exit_status:int, stdout:str, stderr:str).
    """
    import asyncio

    async def _run():
        proc = await conn.run(cmd, check=False, timeout=timeout)
        return proc.exit_status, proc.stdout, proc.stderr

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run())
    finally:
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass


def start_background(conn, cmd: str) -> Optional[int]:
    """Start a background command on the remote host and return its PID when available.

    This uses a simple shell trick to background the process and echo its PID.
    Returns None if the PID could not be parsed.
    """
    # Use `sh -c` so we can echo the pid of the backgrounded process.
    wrapped = f"sh -c '{cmd} > /dev/null 2>&1 & echo $!'"
    try:
        status, out, err = run_command(conn, wrapped)
    except Exception:
        return None
    try:
        pid = int(out.strip().splitlines()[-1]) if out.strip() else None
        return pid
    except Exception:
        return None
