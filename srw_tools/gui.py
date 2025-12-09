"""Small tkinter GUI that lists registered visualizers as buttons.

Design goals:
- Provide a test-friendly factory function `make_visualizer_buttons` that
  doesn't require tkinter so tests can verify behavior in headless CI.
- Provide `build_frame(parent)` which wires those buttons into a tkinter Frame.
- Provide `run_gui()` entry which runs a small app.
"""
from typing import Callable
import json
from pathlib import Path
import socket
import threading
import asyncio

SERVERS_FILE = Path.home() / '.srw_ui_servers.json'


def _load_servers():
    if not SERVERS_FILE.exists():
        return {}
    try:
        with open(SERVERS_FILE, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
            # expect mapping url->info
            return data
    except Exception:
        return {}


def _save_servers(data):
    try:
        # sanitize data to JSON-serializable form (drop private keys and
        # objects that can't be serialized)
        clean = {}
        for url, info in (data or {}).items():
            if not isinstance(info, dict):
                continue
            out = {}
            for k, v in info.items():
                if k.startswith('_'):
                    continue
                try:
                    json.dumps(v)
                except Exception:
                    # skip non-serializable values
                    continue
                out[k] = v
            clean[url] = out

        with open(SERVERS_FILE, 'w', encoding='utf-8') as fh:
            json.dump(clean, fh, indent=2)
    except Exception:
        # ignore errors when writing
        pass


def _find_free_local_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_ssh_server(url: str, path: str, env: str):
    """Attempt to SSH to the host in url, start a server at a free remote port,
    forward it locally and return (local_port, remote_port, conn, listener).

    This function is synchronous (blocks) and will use asyncio internally.
    It requires `asyncssh` to be installed. Caller should run this in a
    background thread to avoid blocking the GUI.
    """
    import asyncssh

    # Basic parsing of user@host:port
    u = url
    user = None
    host = u
    port = 22
    if '@' in u:
        user, host = u.split('@', 1)
    if ':' in host:
        h, p = host.rsplit(':', 1)
        host = h
        try:
            port = int(p)
        except Exception:
            port = 22

    async def _do_connect():
        connect_params = {
            'host': host,
            'port': port,
        }
        if user:
            connect_params['username'] = user
        conn = await asyncssh.connect(**connect_params)

        # pick a remote free port
        proc = await conn.run("python -c 'import socket; s=socket.socket(); s.bind((\"127.0.0.1\",0)); print(s.getsockname()[1]); s.close()'", check=True)
        remote_port = int(proc.stdout.strip())

        # start server remotely and capture the PID of the backgrounded process
        cmd = ""
        if path:
            cmd += f"cd {path} && "
        if env:
            cmd += f"conda run -n {env} "

        cmd += f"python -m srw_tools.rpc_server --host 127.0.0.1 --port {remote_port} > /tmp/srw_server_{remote_port}.log 2>&1 & echo $!'"
        proc = await conn.run(cmd, check=True)
        try:
            pid = int(proc.stdout.strip())
        except Exception:
            pid = None

        local_port = _find_free_local_port()
        listener = await conn.forward_local_port('127.0.0.1', local_port, '127.0.0.1', remote_port)
        return local_port, remote_port, pid, conn, listener

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_do_connect())
    finally:
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass


def stop_ssh_server(url: str, servers: dict):
    """Stop the remote server and tear down the forwarded connection.

    Returns a tuple (success:bool, message:str).
    """
    info = servers.get(url)
    if not info:
        return False, 'No server record'

    conn = info.get('_conn')
    listener = info.get('_listener')
    pid = info.get('pid')
    remote_port = info.get('remote_port')

    if conn is None:
        # no active connection
        return False, 'Not connected'

    async def _do_stop():
        try:
            # try kill by pid first
            if pid:
                await conn.run(f'kill {pid}', check=False)
            elif remote_port:
                # fallback: try to kill by command name
                await conn.run("pkill -f srw_tools.rpc_server", check=False)

            # close listener if present
            if listener and hasattr(listener, 'close'):
                try:
                    listener.close()
                except Exception:
                    pass

            # attempt to close connection
            try:
                c = conn.close()
                # if close() is a coroutine, await it
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


def view_remote_log(url: str, servers: dict):
    """Return text of the remote server log or error message.

    Uses the active SSH connection if present, otherwise falls back to the
    local_proxy (xmlrpc) read_file endpoint.
    """
    info = servers.get(url)
    if not info:
        return False, 'No server record'

    remote_port = info.get('remote_port')
    conn = info.get('_conn')
    local_proxy = info.get('local_proxy')

    if remote_port is None:
        return False, 'No remote port known'

    if conn is not None:
        async def _do_read():
            try:
                proc = await conn.run(f'cat /tmp/srw_server_{remote_port}.log', check=False)
                return True, proc.stdout
            except Exception as e:
                return False, str(e)

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_do_read())
        finally:
            try:
                asyncio.set_event_loop(None)
            except Exception:
                pass

    if local_proxy:
        try:
            import xmlrpc.client

            proxy = xmlrpc.client.ServerProxy(local_proxy)
            content = proxy.read_file(f'/tmp/srw_server_{remote_port}.log')
            return True, content
        except Exception as e:
            return False, str(e)

    return False, 'No way to read remote logs'


def connect_to_server(url: str, path: str, env: str, servers: dict):
    """Connect to a server entry in `servers`.

    - For HTTP/HTTPS-style URLs this just marks the server as "used locally"
      by setting 'local_proxy' to the known client_url so the UI can use it.
    - For SSH style targets (e.g. user@host[:port]) this will call
      start_ssh_server and update the servers mapping with connection info.

    Returns a tuple (ok: bool, message: str, info: dict_or_none)
    """
    if not url:
        return False, 'No url', None

    # Ensure an entry for this url
    servers.setdefault(url, {})
    entry = servers[url]

    # Detect HTTP-style urls and treat them as local/remote RPC endpoints
    if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://')):
        client_url = entry.get('client_url') or url
        entry['local_proxy'] = client_url
        # Make client_url the canonical field for clients to use
        entry['client_url'] = client_url
        _save_servers(servers)
        return True, f'Using local server at {client_url}', {'local_proxy': client_url}

    # Otherwise attempt SSH start
    try:
        lp, remote_port, pid, conn, listener = start_ssh_server(url, path, env)
        # create xmlrpc client pointing at forwarding
        entry['local_proxy'] = f'http://127.0.0.1:{lp}/'
        entry['remote_port'] = remote_port
        entry['pid'] = pid
        entry['_conn'] = conn
        entry['_listener'] = listener
        # align client_url so visualizers will use the forwarded proxy
        entry['client_url'] = entry['local_proxy']
        _save_servers(servers)
        return True, f'Connected (localhost:{lp})', {'local_proxy': entry['local_proxy'], 'remote_port': remote_port, 'pid': pid}
    except Exception as e:
        return False, str(e), None


def disconnect_ssh_server(url: str, servers: dict):
    """Tear down the forwarded SSH connection for this server without killing the remote process."""
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
    info.pop('local_proxy', None)
    _save_servers(servers)
    return True, 'disconnected'


def make_visualizer_buttons(create_button_fn: Callable[[str, Callable], object], *, get_params_fn=None, get_server_fn=None):
    """Create UI buttons for every registered visualizer.

    create_button_fn(name, callback) will be called for each registered
    visualizer name. The callback will instantiate and run the visualizer
    when invoked.

    This function does NOT import tkinter so it can be tested without a
    display by passing a test double for create_button_fn.
    """
    from .visualizer import list_visualizers, get_visualizer

    created = []

    for name in list_visualizers():
        def make_cb(n=name):
            def cb():
                cls = get_visualizer(n)
                inst = cls()

                # Attach a server client if provided so process() can use it.
                if callable(get_server_fn):
                    try:
                        inst.server = get_server_fn(n)
                    except Exception:
                        inst.server = None

                # Get parameters if a provider was supplied
                params = None
                if callable(get_params_fn):
                    try:
                        params = get_params_fn(n)
                    except Exception:
                        params = None

                # Try server/local process -> view pipeline, with fallbacks.
                data = None
                if hasattr(inst, 'process'):
                    try:
                        data = inst.process(params)
                    except NotImplementedError:
                        data = None
                elif hasattr(inst, 'run'):
                    try:
                        data = inst.run(params)
                    except NotImplementedError:
                        data = None

                if hasattr(inst, 'view'):
                    try:
                        return inst.view(parent=None, data=data)
                    except NotImplementedError:
                        pass

                if hasattr(inst, 'show'):
                    try:
                        return inst.show(parent=None, data=data)
                    except NotImplementedError:
                        pass

                if hasattr(inst, 'run'):
                    return inst.run(data)
                return None

            return cb

        created.append(create_button_fn(name, make_cb()))

    return created


def classify_visualizer_output(out):
    """Heuristically categorize visualizer output.

    Returns one of: 'plot' (contains x/y numeric lists), 'image' (2D grid
    or values), or 'text' (anything else).
    """
    if isinstance(out, dict):
        # plot if x and y keys are present and both are list-like
        if 'x' in out and 'y' in out:
            return 'plot'
        if 'grid' in out:
            return 'image'
        # some other dict -> text
        return 'text'

    # numeric sequences could be treated as plots
    try:
        import numpy as _np
    except Exception:
        _np = None

    if _np is not None:
        if _np.ndim(_np.array(out)) == 2:
            return 'image'

    return 'text'


def build_frame(parent):
    """Create a tkinter.Frame with a button for each registered visualizer.

    The parent should be a tkinter container (e.g., Tk or Frame).
    Import tkinter here to avoid import-time display issues when importing
    the module for tests.
    """
    try:
        import tkinter as tk
        from tkinter import messagebox
    except Exception as e:
        raise RuntimeError('tkinter not available') from e

    frame = tk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True)

    def _make_button(name, cb):
        b = tk.Button(frame, text=name, width=20)

        def _onclick():
            try:
                out = cb()
                kind = classify_visualizer_output(out)

                # Create a new window and render using a suitable renderer
                win = tk.Toplevel(frame)
                win.title(f'Visualizer: {name}')

                # plotting renderer if appropriate and matplotlib available
                if kind == 'plot':
                    try:
                        from .gui_helpers import MatplotlibEmbed
                    except Exception:
                        # fallback to text display
                        kind = 'text'

                if kind == 'plot':
                    x = out.get('x')
                    y = out.get('y')
                    def draw(ax):
                        ax.plot(x, y)
                        ax.set_title(name)

                    emb = MatplotlibEmbed(parent=win, figsize=(5,3))
                    emb.create_figure(draw)
                elif kind == 'image':
                    try:
                        from .gui_helpers import MatplotlibEmbed
                    except Exception:
                        kind = 'text'

                    if kind == 'image':
                        grid = out.get('grid') if isinstance(out, dict) else out
                        def draw(ax):
                            ax.imshow(grid, cmap='gray')
                            ax.set_title(name)

                        emb = MatplotlibEmbed(parent=win, figsize=(4,4))
                        emb.create_figure(draw)
                    else:
                        txt = tk.Text(win, wrap='word', height=10)
                        txt.insert('1.0', str(out))
                        txt.config(state='disabled')
                        txt.pack(fill=tk.BOTH, expand=True)
                else:
                    txt = tk.Text(win, wrap='word', height=10)
                    txt.insert('1.0', str(out))
                    txt.config(state='disabled')
                    txt.pack(fill=tk.BOTH, expand=True)

            except Exception as ex:
                messagebox.showerror('Visualizer error', str(ex))

        b.config(command=_onclick)
        b.pack(padx=6, pady=4)
        return b

    # Server management UI: allow adding RPC server endpoints and selecting one
    # load persisted servers and ensure a sensible local default exists
    servers = _load_servers()  # mapping url -> info dict
    DEFAULT_LOCAL = 'http://127.0.0.1:8000/'
    if not servers:
        # create a default local server entry so the GUI selects local machine
        servers[DEFAULT_LOCAL] = {'url': DEFAULT_LOCAL, 'client_url': DEFAULT_LOCAL, 'path': '', 'conda_env': '', 'local_proxy': None}
    server_frame = tk.Frame(frame)
    server_frame.pack(fill=tk.X)
    tk.Label(server_frame, text='RPC server URL:').pack(side=tk.LEFT, padx=(4, 2))
    server_entry = tk.Entry(server_frame)
    server_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    selected_server = tk.StringVar(value='')

    def add_server():
        url = server_entry.get().strip()
        if not url:
            return
        try:
            # store simple record for this URL; keep proxy out of persisted data
            servers[url] = servers.get(url, {})
            servers[url]['url'] = url
            servers[url]['client_url'] = url
            # initially no ssh/forward info
            servers[url].setdefault('path', '')
            servers[url].setdefault('conda_env', '')
            servers[url].setdefault('local_proxy', None)
            # update menu
            menu = server_menu['menu']
            menu.add_command(label=url, command=tk._setit(selected_server, url))
            selected_server.set(url)
            _save_servers(servers)
        except Exception as e:
            messagebox.showerror('Server error', str(e))

    add_button = tk.Button(server_frame, text='Add server', command=add_server)
    add_button.pack(side=tk.LEFT, padx=(0, 4))

    # OptionMenu requires at least one value argument; pass an empty string
    # if there are currently no saved servers so the widget initializes
    initial_values = list(servers.keys())
    if not initial_values:
        initial_values = [DEFAULT_LOCAL]
        # ensure the mapping exists
        servers.setdefault(DEFAULT_LOCAL, {'url': DEFAULT_LOCAL, 'client_url': DEFAULT_LOCAL, 'path': '', 'conda_env': '', 'local_proxy': None})
    server_menu = tk.OptionMenu(server_frame, selected_server, *initial_values)
    server_menu.pack(side=tk.LEFT)

    # details for selected server: path, conda env, connect
    details_frame = tk.Frame(frame)
    details_frame.pack(fill=tk.X, pady=(6, 4))

    tk.Label(details_frame, text='Path:').pack(side=tk.LEFT, padx=(4, 2))
    path_entry = tk.Entry(details_frame)
    path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    tk.Label(details_frame, text='Conda env:').pack(side=tk.LEFT, padx=(4, 2))
    env_entry = tk.Entry(details_frame, width=12)
    env_entry.pack(side=tk.LEFT, padx=(0, 6))

    status_label = tk.Label(details_frame, text='')
    status_label.pack(side=tk.LEFT, padx=(6, 4))

    def _on_server_select(*args):
        url = selected_server.get()
        if not url:
            path_entry.delete(0, tk.END)
            env_entry.delete(0, tk.END)
            return
        entry = servers.get(url, {})
        path_entry.delete(0, tk.END)
        path_entry.insert(0, entry.get('path', ''))
        env_entry.delete(0, tk.END)
        env_entry.insert(0, entry.get('conda_env', ''))
        # update button labels / states for selected server
        _update_server_buttons()

    selected_server.trace_add('write', _on_server_select)

    def _update_server_buttons():
        """Update the connect/stop/disconnect buttons based on selected server.

        - HTTP/HTTPS entries present a 'Use server' button (no SSH action)
        - Non-http entries show 'Connect via SSH'
        Buttons to stop/disconnect are only enabled when an active SSH connection
        is present on the selected server entry.
        """
        url = selected_server.get()
        if not url:
            connect_button.config(text='Connect', state='disabled')
            stop_button.config(state='disabled')
            disconnect_button.config(state='disabled')
            return

        entry = servers.get(url, {})
        # If server already has a _conn (active ssh connection)
        connected = bool(entry.get('_conn'))

        if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://')):
            connect_button.config(text='Use server', state='normal')
            # we don't manage remote process for plain HTTP entries
            stop_button.config(state='disabled')
            # only allow disconnect if we've added a local_proxy ourselves
            disconnect_button.config(state='normal' if entry.get('local_proxy') else 'disabled')
        else:
            connect_button.config(text='Connect via SSH', state='normal')
            stop_button.config(state='normal' if connected else 'disabled')
            disconnect_button.config(state='normal' if connected else 'disabled')


    def _connect_to_selected():
        url = selected_server.get()
        if not url:
            messagebox.showwarning('No server selected', 'Please select a server')
            return
        path = path_entry.get().strip()
        env = env_entry.get().strip()
        servers[url]['path'] = path
        servers[url]['conda_env'] = env
        _save_servers(servers)
        status_label.config(text='Connecting...')

        # non-blocking connect using the connect_to_server helper (run in background thread)
        def _worker():
            try:
                ok, msg, info = connect_to_server(url, path, env, servers)
                if ok:
                    status_label.config(text=msg)
                else:
                    status_label.config(text='Connect failed')
                    messagebox.showerror('Connect failed', msg)
            except Exception as e:
                status_label.config(text='Connect failed')
                messagebox.showerror('SSH error', str(e))
            finally:
                # refresh button states after attempted connection
                try:
                    _update_server_buttons()
                except Exception:
                    pass

        th = threading.Thread(target=_worker, daemon=True)
        th.start()

    connect_button = tk.Button(details_frame, text='Connect via SSH', command=_connect_to_selected)
    connect_button.pack(side=tk.LEFT, padx=(6, 4))

    def _show_logs():
        url = selected_server.get()
        if not url:
            messagebox.showwarning('No server selected', 'Please select a server')
            return

        status_label.config(text='Fetching logs...')

        def _worker_logs():
            ok, out = view_remote_log(url, servers)
            if ok:
                # show in a scrollable window
                win = tk.Toplevel(frame)
                win.title(f'Logs for {url}')
                txt = tk.Text(win, wrap='none')
                txt.insert('1.0', out)
                txt.config(state='disabled')
                txt.pack(fill=tk.BOTH, expand=True)
                status_label.config(text='')
            else:
                status_label.config(text='Log fetch failed')
                messagebox.showerror('Log fetch failed', out)

        threading.Thread(target=_worker_logs, daemon=True).start()

    def _stop_server():
        url = selected_server.get()
        if not url:
            messagebox.showwarning('No server selected', 'Please select a server')
            return

        if not messagebox.askyesno('Confirm stop', f'Stop remote server at {url}?'):
            return

        status_label.config(text='Stopping...')

        def _worker_stop():
            ok, msg = stop_ssh_server(url, servers)
            if ok:
                # clear connection info
                info = servers.get(url, {})
                info.pop('_conn', None)
                info.pop('_listener', None)
                info.pop('local_proxy', None)
                info.pop('remote_port', None)
                info.pop('pid', None)
                _save_servers(servers)
                status_label.config(text='Stopped')
                messagebox.showinfo('Stopped', f'Server at {url} stopped')
            else:
                status_label.config(text='Stop failed')
                messagebox.showerror('Stop failed', msg)

        threading.Thread(target=_worker_stop, daemon=True).start()

    stop_button = tk.Button(details_frame, text='Stop server', command=_stop_server)
    stop_button.pack(side=tk.LEFT, padx=(6, 4))

    logs_button = tk.Button(details_frame, text='Show logs', command=_show_logs)
    logs_button.pack(side=tk.LEFT, padx=(6, 4))

    def _inspect_server():
        url = selected_server.get()
        if not url:
            messagebox.showwarning('No server selected', 'Please select a server')
            return
        info = servers.get(url, {})
        details = []
        details.append(f"URL: {url}")
        details.append(f"Local proxy: {info.get('local_proxy')}")
        details.append(f"Remote port: {info.get('remote_port')}")
        details.append(f"PID: {info.get('pid')}")
        details.append(f"Conda env: {info.get('conda_env')}")
        details.append(f"Path: {info.get('path')}")
        # connection present?
        details.append(f"Connected: {'_conn' in info and info.get('_conn') is not None}")
        messagebox.showinfo('Server info', '\n'.join(details))

    inspect_button = tk.Button(details_frame, text='Inspect', command=_inspect_server)
    inspect_button.pack(side=tk.LEFT, padx=(6, 4))

    def _disconnect_server():
        url = selected_server.get()
        if not url:
            messagebox.showwarning('No server selected', 'Please select a server')
            return
        info = servers.get(url, {})
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
                    # run it synchronously
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
        info.pop('local_proxy', None)
        _save_servers(servers)
        status_label.config(text='Disconnected')

    disconnect_button = tk.Button(details_frame, text='Disconnect', command=_disconnect_server)
    disconnect_button.pack(side=tk.LEFT, padx=(6, 4))

    # Provide a GUI-backed parameters form and server selector for use by
    # the visualizer factory.
    def gui_get_params(name):
        cls = get_visualizer(name)
        inst = cls()
        params_schema = inst.parameters() if hasattr(inst, 'parameters') else []
        if not params_schema:
            return None

        # Popup dialog to collect params
        dlg = tk.Toplevel(frame)
        dlg.title(f'Parameters for {name}')
        entries = {}

        for p in params_schema:
            lbl = tk.Label(dlg, text=p.get('label') or p['name'])
            lbl.pack(fill=tk.X, padx=6)
            ent = tk.Entry(dlg)
            ent.pack(fill=tk.X, padx=6, pady=(0, 6))
            default = p.get('default')
            if default is not None:
                ent.insert(0, str(default))
            entries[p['name']] = (ent, p['type'])

        result = {'ok': False, 'vals': None}

        def on_ok():
            vals = {}
            for key, (ent, t) in entries.items():
                v = ent.get()
                if t == 'int':
                    try:
                        vals[key] = int(v)
                    except Exception:
                        vals[key] = None
                elif t == 'float':
                    try:
                        vals[key] = float(v)
                    except Exception:
                        vals[key] = None
                elif t == 'bool':
                    vals[key] = v.lower() in ('1', 'true', 'yes', 'on')
                else:
                    vals[key] = v

            result['ok'] = True
            result['vals'] = vals
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(fill=tk.X, pady=6)
        tk.Button(btn_frame, text='OK', command=on_ok).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text='Cancel', command=on_cancel).pack(side=tk.LEFT, padx=6)

        # Wait for dialog to close
        frame.wait_window(dlg)
        return result['vals'] if result['ok'] else None

    def gui_get_server(name):
        url = selected_server.get()
        return servers.get(url)

    # build buttons using the shared factory, wiring GUI param and server callbacks
    make_visualizer_buttons(lambda n, cb: _make_button(n, cb), get_params_fn=gui_get_params, get_server_fn=gui_get_server)

    return frame


def run_gui():
    """Run the GUI as a small standalone app.

    This is intentionally tiny and synchronous. The function returns when
    the Tk mainloop finishes.
    """
    try:
        import tkinter as tk
    except Exception as e:
        raise RuntimeError('tkinter not available') from e

    root = tk.Tk()
    root.title('SRW visualizers')
    build_frame(root)
    root.mainloop()


if __name__ == '__main__':
    run_gui()
