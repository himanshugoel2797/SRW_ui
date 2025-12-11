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
    """Establish an SSH connection to the given url and return connection info.

    Returns a tuple `(local_port, remote_port, pid, conn, listener)` where
    `conn` is an active connection object usable with `ssh_helper.run_command`.
    """
    from .ssh_helper import connect_sync

    # connect_sync will parse user@host:port itself
    conn = connect_sync(url)
    # We don't start any remote server by default; return conn for caller
    return None, None, None, conn, None


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
    """Return the remote server log text via SSH.

    The server entry must include `_conn` (active SSH connection) and
    `remote_log` (path to the log file on the remote host).
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

    # use ssh_helper for synchronous execution
    try:
        from .ssh_helper import run_command
        status, out, err = run_command(conn, f"cat {remote_log}")
        if status == 0:
            return True, out
        return False, err or 'Failed to read remote log'
    except Exception as e:
        return False, str(e)


def connect_to_server(url: str, path: str, env: str, servers: dict):
    """Connect to a server entry in `servers`.

    For SSH style targets (e.g. user@host[:port]) this will call
    start_ssh_server and update the servers mapping with connection info.

    Returns a tuple (ok: bool, message: str, info: dict_or_none)
    """
    if not url:
        return False, 'No url', None

    # Ensure an entry for this url
    servers.setdefault(url, {})
    entry = servers[url]

    # Enforce single active SSH connection: if another server is connected,
    # disconnect it first so only one `_conn` exists at a time.
    try:
        existing = next((u for u, info in servers.items() if info.get('_conn')), None)
        if existing and existing != url:
            # best-effort disconnect of existing connection
            try:
                disconnect_ssh_server(existing, servers)
            except Exception:
                # swallow errors and continue to attempt new connection
                pass
    except Exception:
        pass

    # Attempt SSH start
    try:
        lp, remote_port, pid, conn, listener = start_ssh_server(url, path, env)
        # store connection info for later remote operations
        entry['pid'] = pid
        entry['_conn'] = conn
        entry['_listener'] = listener
        entry['remote_host'] = url
        _save_servers(servers)
        return True, f'Connected via SSH to {url}', {'remote_host': url, 'pid': pid}
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

                # Get parameters if a provider was supplied - GUI only provides
                # the parameter dictionary. Visualizers are responsible for
                # processing and managing their own windows.
                params = None
                if callable(get_params_fn):
                    try:
                        params = get_params_fn(n)
                    except Exception:
                        params = None

                # Prefer calling view(data=params) and let the visualizer
                # decide whether to process or render. If view is absent or
                # not implemented, fall back to process(params).
                if hasattr(inst, 'view'):
                    try:
                        # Launch the visualizer's view and do not assume it
                        # returns processed data — visualizers manage their
                        # own windows and side-effects.
                        inst.view(data=params)
                        return None
                    except NotImplementedError:
                        pass

                if hasattr(inst, 'process'):
                    try:
                        return inst.process(params)
                    except NotImplementedError:
                        return None

                return None

            return cb

        created.append(create_button_fn(name, make_cb()))

    return created


def list_visualizers_by_group():
    """Return a mapping of group_name -> list of visualizer names.

    Useful for tests and UI layout logic. Groups are determined using
    each visualizer's `get_group()` (or `group` attribute); missing
    groups collapse to 'Other'.
    """
    from .visualizer import list_visualizers, get_visualizer

    groups = {}
    for name in list_visualizers():
        try:
            cls = get_visualizer(name)
            try:
                inst = cls()
                grp = inst.get_group() if hasattr(inst, 'get_group') else getattr(cls, 'group', None) or 'Other'
            except Exception:
                grp = getattr(cls, 'group', None) or 'Other'
        except Exception:
            grp = 'Other'

        groups.setdefault(grp, []).append(name)

    # keep the lists stable/sorted for consistent UI and tests
    return {g: sorted(names) for g, names in groups.items()}


from .simulation_scripts import script_manager


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
        from tkinter import messagebox, filedialog
    except Exception as e:
        raise RuntimeError('tkinter not available') from e

    frame = tk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True)

    def _make_button(name, cb, parent=None):
        # Use the visualizer's human-friendly display name when available
        try:
            from .visualizer import get_visualizer
            try:
                cls = get_visualizer(name)
                try:
                    inst = cls()
                    if hasattr(inst, 'get_display_name'):
                        label = inst.get_display_name()
                    else:
                        label = getattr(cls, 'display_name', None) or name
                except Exception:
                    # if instantiation fails, fall back to class attribute or raw name
                    label = getattr(cls, 'display_name', None) or name
            except Exception:
                label = name
        except Exception:
            label = name

        parent = parent or frame
        b = tk.Button(parent, text=label, width=20)

        def _onclick():
            try:
                # Visualizers own their presentation; GUI only launches them
                # and passes the parameter dict. The visualizer may return
                # processed data or manage its own windows.
                return cb()
            except Exception as ex:
                messagebox.showerror('Visualizer error', str(ex))

        b.config(command=_onclick)
        b.pack(padx=6, pady=4)
        return b

    # Server management UI: allow adding SSH server targets and selecting one
    servers = _load_servers()  # mapping url -> info dict
    server_frame = tk.Frame(frame)
    server_frame.pack(fill=tk.X)
    tk.Label(server_frame, text='SSH Target (user@host):').pack(side=tk.LEFT, padx=(4, 2))
    server_entry = tk.Entry(server_frame)
    server_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    selected_server = tk.StringVar(value='')


    # OptionMenu requires at least one value argument
    initial_values = list(servers.keys()) if servers else ['']
    # select a sensible default so the details pane is populated
    if initial_values and initial_values[0]:
        selected_server.set(initial_values[0])
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

        # If any server has an active connection, we only allow actions on
        # that server. This enforces a single active SSH connection at a time.
        active = next((u for u, info in servers.items() if info.get('_conn')), None)
        if active is None:
            # no active connection anywhere
            connect_button.config(text='Connect via SSH', state='normal')
            stop_button.config(state='normal' if connected else 'disabled')
            disconnect_button.config(state='normal' if connected else 'disabled')
        elif active == url:
            # the selected server is the one connected
            connect_button.config(text='Connected', state='disabled')
            stop_button.config(state='normal')
            disconnect_button.config(state='normal')
        else:
            # another server is connected — do not allow connect/stop on this one
            connect_button.config(text=f'Connected: {active}', state='disabled')
            stop_button.config(state='disabled')
            disconnect_button.config(state='disabled')


    def _connect_to_selected():
        # Allow the user to either select a server from history or type a new
        # target into the `server_entry` field. If a typed target is present
        # it takes precedence and will be added to history after a successful
        # connection.
        typed = server_entry.get().strip()
        url = typed or selected_server.get()
        if not url:
            messagebox.showwarning('No server selected', 'Please select or type a server')
            return
        path = path_entry.get().strip()
        env = env_entry.get().strip()

        # Ensure a record exists for this URL so connect_to_server can store
        # connection info. We'll add to the OptionMenu on success.
        if url not in servers:
            servers[url] = {'url': url, 'path': path, 'conda_env': env}
        else:
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
                    # Rebuild the OptionMenu so the most-recently-used server
                    # appears first. This avoids duplicates and keeps ordering
                    # consistent with recent use.
                    try:
                        menu = server_menu['menu']
                        # Build an ordered list with the current url first,
                        # followed by the other known servers in their
                        # existing order.
                        ordered = [url] + [k for k in list(servers.keys()) if k != url]
                        # clear and repopulate menu
                        menu.delete(0, 'end')
                        for label in ordered:
                            menu.add_command(label=label, command=tk._setit(selected_server, label))
                        # make sure the selection reflects the connected server
                        selected_server.set(url)
                        # Reorder the in-memory `servers` mapping to match the
                        # recent-first ordering and persist it so the file on
                        # disk reflects the same ordering.
                        try:
                            ordered_servers = {k: servers.get(k, {}) for k in ordered}
                            servers.clear()
                            servers.update(ordered_servers)
                            _save_servers(servers)
                        except Exception:
                            # if reordering/persistence fails, continue silently
                            pass
                    except Exception:
                        pass
                    # clear the typed entry once added/successful
                    try:
                        server_entry.delete(0, tk.END)
                    except Exception:
                        pass
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
        details.append(f"Remote host: {info.get('remote_host')}")
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
        _save_servers(servers)
        status_label.config(text='Disconnected')

    disconnect_button = tk.Button(details_frame, text='Disconnect', command=_disconnect_server)
    disconnect_button.pack(side=tk.LEFT, padx=(6, 4))

    def gui_get_server(name):
        url = selected_server.get()
        return servers.get(url)

    # Create grouped sections for visualizers so the UI is easier to
    # navigate when many visualizers are available.
    # We'll map visualizer name -> group and create a frame per group.
    from .visualizer import list_visualizers, get_visualizer

    name_to_group = {}
    groups = {}
    for name in list_visualizers():
        try:
            cls = get_visualizer(name)
            try:
                inst = cls()
                grp = inst.get_group() if hasattr(inst, 'get_group') else getattr(cls, 'group', None) or 'Other'
            except Exception:
                grp = getattr(cls, 'group', None) or 'Other'
        except Exception:
            grp = 'Other'

        name_to_group[name] = grp
        groups.setdefault(grp, []).append(name)

    # create a horizontal container for grouped visualizers
    groups_container = tk.Frame(frame)
    groups_container.pack(fill=tk.BOTH, expand=True, pady=(6, 4))

    # mapping of group to frame for placing buttons
    group_frames = {}
    # create a header + content frame for each group and make the content
    # collapsible. We keep references to the toggle button and content
    # frame so tests can access and simulate toggles.
    group_buttons = {}
    group_collapsed = {}
    for grp in sorted(groups.keys()):
        header = tk.Frame(groups_container)
        header.pack(fill=tk.X, padx=6, pady=(4, 0))

        # toggle button: '-' means expanded, '+' means collapsed
        def _make_toggle(g):
            def _toggle():
                btn = group_buttons[g]
                content = group_frames[g]
                collapsed = group_collapsed.get(g, False)
                if collapsed:
                    # show it
                    content.pack(fill=tk.X, padx=6, pady=(0, 6))
                    btn.config(text='-')
                    group_collapsed[g] = False
                else:
                    # hide it
                    content.pack_forget()
                    btn.config(text='+')
                    group_collapsed[g] = True

            return _toggle

        btn = tk.Button(header, text='-', width=2, command=_make_toggle(grp))
        btn.pack(side=tk.LEFT)
        tk.Label(header, text=grp).pack(side=tk.LEFT, padx=(6, 0))

        gf = tk.Frame(groups_container)
        gf.pack(fill=tk.X, padx=6, pady=(0, 6))
        # store convenient attributes for tests
        gf._group_name = grp
        gf._toggle_button = btn

        group_frames[grp] = gf
        # add a group divider below this group's content for visual separation
        try:
            gdiv = tk.Frame(groups_container, height=2, bg='black')
            gdiv.pack(fill=tk.X, padx=4, pady=(2, 6))
            gdiv._is_group_divider = True
        except Exception:
            pass
        group_buttons[grp] = btn
        group_collapsed[grp] = False

    # mapping name -> callable that returns current params from inline widgets
    param_getters = {}

    def grouped_factory(name, cb):
        parent_for_name = group_frames.get(name_to_group.get(name, 'Other'))

        # create a row container for button + inline params
        row = tk.Frame(parent_for_name)
        row.pack(fill=tk.X, pady=(2, 2))

        # expose the visualizer name on the row for tests/inspection
        row._vis_name = name

        # create a column container inside the row: parameters above, button below
        col = tk.Frame(row)
        col.pack(fill=tk.X)

        # pack params first into col so they appear above the button
        # keep callback reference for tests (make_visualizer_buttons will still
        # call the passed callback when the user activates the UI)
        row._callback = cb

        # Create inline parameter widgets (if the visualizer exposes parameters())
        try:
            cls = get_visualizer(name)
            try:
                inst = cls()
                schema = inst.parameters() if hasattr(inst, 'parameters') else []
            except Exception:
                schema = getattr(cls, 'parameters', []) or []
        except Exception:
            schema = []

        # map param name -> (widget_or_var, type)
        row._param_widgets = {}
        if schema:
            # pack params next to the button
            params_frame = tk.Frame(col)
            params_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6,0))
            # allow multiple stacked sub-rows inside params_frame so
            # 'newline' parameter type can break params into new lines
            param_rows = []
            def _new_param_row():
                r = tk.Frame(params_frame)
                r.pack(fill=tk.X, anchor='w')
                param_rows.append(r)
                return r

            current_param_row = _new_param_row()
            # expose param_rows for tests and introspection
            row._param_rows = param_rows
            row._param_labels = {}
            for p in schema:
                pname = p['name']
                ptype = p.get('type')
                plabel_text = p.get('label') or pname
                # if this param explicitly requests a newline, create a
                # fresh parameter sub-row and mark the param as a newline
                if ptype == 'newline':
                    current_param_row = _new_param_row()
                    row._param_widgets[pname] = (None, 'newline')
                    row._param_labels[pname] = None
                    continue
                # show small label next to the parameter widget
                try:
                    lab = tk.Label(current_param_row, text=plabel_text)
                    lab.pack(side=tk.LEFT, padx=(2, 2))
                    row._param_labels[pname] = lab
                except Exception:
                    pass
                if ptype == 'bool':
                    var = tk.BooleanVar(value=bool(p.get('default')))
                    cbw = tk.Checkbutton(current_param_row, text=p.get('label', pname), variable=var)
                    cbw.pack(side=tk.LEFT, padx=(4,2))
                    row._param_widgets[pname] = (var, 'bool')
                elif ptype == 'simulation':
                    # OptionMenu of discovered simulation scripts
                    try:
                        sims = script_manager.list_simulation_scripts()
                    except Exception:
                        sims = {}

                    paths = sorted(sims.keys())
                    default = p.get('default') or ''
                    selected_path = ''
                    # Determine selected path if default provided (path or name)
                    if default in paths:
                        selected_path = default
                    else:
                        for path, _name in sims.items():
                            if _name == default:
                                selected_path = path
                                break
                    if not selected_path and paths:
                        selected_path = paths[0]

                    # Two variables: display_var for OptionMenu display, and
                    # value_var to hold the canonical path value used by code.
                    value_var = tk.StringVar(value=selected_path)
                    display_var = tk.StringVar(value=(f"{Path(selected_path).name} — {sims.get(selected_path) or ''}" if selected_path else ''))
                    if paths:
                        opt = tk.OptionMenu(current_param_row, display_var, *[f"{Path(p).name} — {sims.get(p) or ''}" for p in paths])
                        # Build menu entries to update both variables when chosen
                        try:
                            menu = opt['menu']
                            menu.delete(0, 'end')
                            for path in paths:
                                label = sims.get(path) or ''
                                display = f"{Path(path).name} — {label}" if label else Path(path).name
                                def _make_cmd(p=path, d=display):
                                    def _cmd():
                                        display_var.set(d)
                                        value_var.set(p)
                                    return _cmd
                                menu.add_command(label=display, command=_make_cmd())
                        except Exception:
                            pass
                        opt.pack(side=tk.LEFT, padx=(4,2))
                    else:
                        lbl = tk.Label(current_param_row, text='(no sims)')
                        lbl.pack(side=tk.LEFT, padx=(4,2))
                    row._param_widgets[pname] = (value_var, 'simulation')
                elif ptype in ('file', 'directory'):
                    sval = tk.StringVar(value=p.get('default') or '')
                    ent = tk.Entry(current_param_row, textvariable=sval, width=24)
                    ent.pack(side=tk.LEFT, padx=(4, 2))

                    def _browse(pt=ptype, var=sval):
                        try:
                            if pt == 'file':
                                res = filedialog.askopenfilename()
                            else:
                                res = filedialog.askdirectory()
                            if res:
                                var.set(res)
                        except Exception:
                            pass

                    b = tk.Button(current_param_row, text='Browse', command=_browse)
                    b.pack(side=tk.LEFT, padx=(0, 4))
                    row._param_widgets[pname] = (sval, ptype)
                else:
                    ent = tk.Entry(current_param_row, width=12)
                    default = p.get('default')
                    if default is not None:
                        ent.insert(0, str(default))
                    ent.pack(side=tk.LEFT, padx=(4,2))
                    row._param_widgets[pname] = (ent, ptype or 'str')

        # create the main button inside the column after parameters so
        # the parameters appear above the button
        btn = _make_button(name, cb, parent=col)
        row._button = btn

        # register a getter for this visualizer's params
        def _getter():
            vals = {}
            for k, w in row._param_widgets.items():
                widget, ptype = w
                if ptype == 'newline':
                    # newline is a layout marker, not an actual param value
                    continue
                try:
                    raw = widget.get()
                except Exception:
                    raw = None

                # coerce according to type
                if ptype == 'int':
                    try:
                        vals[k] = int(raw)
                    except Exception:
                        vals[k] = None
                elif ptype == 'float':
                    try:
                        vals[k] = float(raw)
                    except Exception:
                        vals[k] = None
                elif ptype == 'bool':
                    vals[k] = bool(raw)
                else:
                    vals[k] = raw
            return vals if vals else None

        # add a thin divider below this row for visual separation
        try:
            div = tk.Frame(parent_for_name, height=1, bg='gray')
            div.pack(fill=tk.X, padx=6, pady=(0, 4))
            div._is_divider = True
        except Exception:
            pass

        param_getters[name] = _getter
        return row

    # pass our inline param getter so callbacks use the widgets next to
    # each button instead of opening a popup.
    def _inline_get_params(n):
        return param_getters.get(n, lambda: None)()

    make_visualizer_buttons(grouped_factory, get_params_fn=_inline_get_params, get_server_fn=gui_get_server)

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
