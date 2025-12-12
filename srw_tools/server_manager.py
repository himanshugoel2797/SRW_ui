"""Server connection manager for SSH-based remote execution.

Provides a centralized interface for managing SSH connections to remote
servers, including connection establishment, lifecycle management, and
persistence of server configurations.
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, Tuple, Optional, Any


SERVERS_FILE = Path.home() / '.srw_ui_servers.json'


def load_servers() -> Dict[str, Any]:
    """Load saved server configurations from disk."""
    if not SERVERS_FILE.exists():
        return {}
    try:
        with open(SERVERS_FILE, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_servers(servers: Dict[str, Any]) -> None:
    """Persist server configurations to disk."""
    try:
        clean = {}
        for url, info in (servers or {}).items():
            if not isinstance(info, dict):
                continue
            out = {}
            for k, v in info.items():
                if k.startswith('_'):
                    continue
                try:
                    json.dumps(v)
                except Exception:
                    continue
                out[k] = v
            clean[url] = out

        with open(SERVERS_FILE, 'w', encoding='utf-8') as fh:
            json.dump(clean, fh, indent=2)
    except Exception:
        pass


def start_ssh_connection(url: str, path: str, env: str) -> Tuple[Optional[int], Optional[int], Optional[int], Any, Any]:
    """Establish SSH connection to the given url.

    Returns a tuple (local_port, remote_port, pid, conn, listener) where
    conn is an active connection object usable with ssh_helper.run_command.
    """
    from .ssh_helper import connect_sync
    conn = connect_sync(url)
    return None, None, None, conn, None


def stop_ssh_connection(url: str, servers: Dict[str, Any]) -> Tuple[bool, str]:
    """Stop the remote server and tear down the connection.

    Returns (success: bool, message: str).
    """
    info = servers.get(url)
    if not info:
        return False, 'No server record'

    conn = info.get('_conn')
    listener = info.get('_listener')
    pid = info.get('pid')

    if conn is None:
        return False, 'Not connected'

    async def _do_stop():
        try:
            if pid:
                await conn.run(f'kill {pid}', check=False)

            if listener and hasattr(listener, 'close'):
                try:
                    listener.close()
                except Exception:
                    pass

            try:
                c = conn.close()
                if asyncio.iscoroutine(c):
                    await c
            except Exception:
                pass

            return True, 'stopped'
        except Exception as e:
            return False, str(e)

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_do_stop())
    finally:
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass


def disconnect_ssh_connection(url: str, servers: Dict[str, Any]) -> Tuple[bool, str]:
    """Tear down the SSH connection without killing the remote process."""
    info = servers.get(url)
    if not info:
        return False, 'No server record'

    conn = info.get('_conn')
    listener = info.get('_listener')

    if listener and hasattr(listener, 'close'):
        try:
            listener.close()
        except Exception:
            pass

    if conn:
        try:
            c = conn.close()
            if asyncio.iscoroutine(c):
                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(c)
                finally:
                    try:
                        asyncio.set_event_loop(None)
                    except Exception:
                        pass
        except Exception:
            pass

    info.pop('_conn', None)
    info.pop('_listener', None)
    save_servers(servers)
    return True, 'disconnected'


def view_remote_log(url: str, servers: Dict[str, Any]) -> Tuple[bool, str]:
    """Retrieve remote server log via SSH.

    Returns (success: bool, log_content_or_error: str).
    """
    info = servers.get(url)
    if not info:
        return False, 'No server record'
    
    conn = info.get('_conn')
    remote_log = info.get('remote_log')

    if conn is None:
        return False, 'Not connected via SSH'

    if not remote_log:
        return False, 'No remote log path configured'

    try:
        from .ssh_helper import run_command
        status, out, err = run_command(conn, f"cat {remote_log}")
        if status == 0:
            return True, out
        return False, err or 'Failed to read remote log'
    except Exception as e:
        return False, str(e)


def connect_to_server(url: str, path: str, env: str, servers: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Connect to a server entry in servers.

    Returns (ok: bool, message: str, info: dict_or_none).
    
    TODO: Review single-connection enforcement logic and consider supporting multiple connections.
    """
    if not url:
        return False, 'No url', None

    servers.setdefault(url, {})
    entry = servers[url]

    try:
        existing = next((u for u, info in servers.items() if info.get('_conn')), None)
        if existing and existing != url:
            try:
                disconnect_ssh_connection(existing, servers)
            except Exception:
                pass
    except Exception:
        pass

    try:
        lp, remote_port, pid, conn, listener = start_ssh_connection(url, path, env)
        entry['pid'] = pid
        entry['_conn'] = conn
        entry['_listener'] = listener
        entry['remote_host'] = url
        save_servers(servers)
        return True, f'Connected via SSH to {url}', {'remote_host': url, 'pid': pid}
    except Exception as e:
        return False, str(e), None
