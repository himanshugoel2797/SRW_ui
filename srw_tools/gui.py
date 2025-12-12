"""Small tkinter GUI that lists registered visualizers as buttons.

Provides a test-friendly factory function `make_visualizer_buttons` and
integration with remote SSH servers for executing visualizations remotely.
"""
from typing import Callable
from pathlib import Path
import threading

from .server_manager import (
    load_servers, save_servers, start_ssh_connection, stop_ssh_connection,
    disconnect_ssh_connection, view_remote_log, connect_to_server
)
from .parameter_widgets import create_parameter_widgets, create_parameter_getter
from . import simulation_scripts


def make_visualizer_buttons(create_button_fn: Callable[[str, Callable], object], *, get_params_fn=None, get_server_fn=None):
    """Create UI buttons for every registered visualizer.

    create_button_fn(name, callback) will be called for each registered
    visualizer name. The callback will instantiate and run the visualizer
    when invoked.
    """
    from .visualizer import list_visualizers, get_visualizer

    created = []

    for name in list_visualizers():
        def make_cb(n=name):
            def cb():
                cls = get_visualizer(n)
                inst = cls()

                if callable(get_server_fn):
                    try:
                        inst.server = get_server_fn(n)
                    except Exception:
                        inst.server = None

                params = None
                if callable(get_params_fn):
                    try:
                        params = get_params_fn(n)
                    except Exception:
                        params = None

                if hasattr(inst, 'view'):
                    try:
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
    """Return a mapping of group_name -> list of visualizer names."""
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

    return {g: sorted(names) for g, names in groups.items()}


def classify_visualizer_output(out):
    """Heuristically categorize visualizer output.

    Returns 'plot', 'image', or 'text'.
    """
    if isinstance(out, dict):
        if 'x' in out and 'y' in out:
            return 'plot'
        if 'grid' in out:
            return 'image'
        return 'text'

    try:
        import numpy as _np
        if _np.ndim(_np.array(out)) == 2:
            return 'image'
    except Exception:
        pass

    return 'text'


def build_frame(parent):
    """Create a tkinter.Frame with a button for each registered visualizer."""
    try:
        import tkinter as tk
        from tkinter import messagebox, filedialog
        import asyncio
    except Exception as e:
        raise RuntimeError('tkinter not available') from e

    frame = tk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True)

    def _make_button(name, cb, parent=None):
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
                    label = getattr(cls, 'display_name', None) or name
            except Exception:
                label = name
        except Exception:
            label = name

        parent = parent or frame
        b = tk.Button(parent, text=label, width=20)

        def _onclick():
            try:
                return cb()
            except Exception as ex:
                messagebox.showerror('Visualizer error', str(ex))

        b.config(command=_onclick)
        b.pack(padx=6, pady=4)
        return b

    servers = load_servers()
    server_frame = tk.Frame(frame)
    server_frame.pack(fill=tk.X)
    tk.Label(server_frame, text='SSH Target (user@host):').pack(side=tk.LEFT, padx=(4, 2))
    server_entry = tk.Entry(server_frame)
    server_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    selected_server = tk.StringVar(value='')

    initial_values = list(servers.keys()) if servers else ['']
    if initial_values and initial_values[0]:
        selected_server.set(initial_values[0])
    server_menu = tk.OptionMenu(server_frame, selected_server, *initial_values)
    server_menu.pack(side=tk.LEFT)

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
        _update_server_buttons()

    selected_server.trace_add('write', _on_server_select)

    def _update_server_buttons():
        """Update button states based on selected server connection status."""
        url = selected_server.get()
        if not url:
            connect_button.config(text='Connect', state='disabled')
            stop_button.config(state='disabled')
            disconnect_button.config(state='disabled')
            return

        entry = servers.get(url, {})
        connected = bool(entry.get('_conn'))

        active = next((u for u, info in servers.items() if info.get('_conn')), None)
        if active is None:
            connect_button.config(text='Connect via SSH', state='normal')
            stop_button.config(state='normal' if connected else 'disabled')
            disconnect_button.config(state='normal' if connected else 'disabled')
        elif active == url:
            connect_button.config(text='Connected', state='disabled')
            stop_button.config(state='normal')
            disconnect_button.config(state='normal')
        else:
            connect_button.config(text=f'Connected: {active}', state='disabled')
            stop_button.config(state='disabled')
            disconnect_button.config(state='disabled')


    def _connect_to_selected():
        typed = server_entry.get().strip()
        url = typed or selected_server.get()
        if not url:
            messagebox.showwarning('No server selected', 'Please select or type a server')
            return
        path = path_entry.get().strip()
        env = env_entry.get().strip()

        if url not in servers:
            servers[url] = {'url': url, 'path': path, 'conda_env': env}
        else:
            servers[url]['path'] = path
            servers[url]['conda_env'] = env
        save_servers(servers)
        status_label.config(text='Connecting...')

        def _worker():
            try:
                ok, msg, info = connect_to_server(url, path, env, servers)
                if ok:
                    status_label.config(text=msg)
                    try:
                        menu = server_menu['menu']
                        ordered = [url] + [k for k in list(servers.keys()) if k != url]
                        menu.delete(0, 'end')
                        for label in ordered:
                            menu.add_command(label=label, command=tk._setit(selected_server, label))
                        selected_server.set(url)
                        try:
                            ordered_servers = {k: servers.get(k, {}) for k in ordered}
                            servers.clear()
                            servers.update(ordered_servers)
                            save_servers(servers)
                        except Exception:
                            pass
                    except Exception:
                        pass
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
            ok, msg = stop_ssh_connection(url, servers)
            if ok:
                info = servers.get(url, {})
                info.pop('_conn', None)
                info.pop('_listener', None)
                info.pop('remote_port', None)
                info.pop('pid', None)
                save_servers(servers)
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

    param_getters = {}

    def grouped_factory(name, cb):
        parent_for_name = group_frames.get(name_to_group.get(name, 'Other'))

        row = tk.Frame(parent_for_name)
        row.pack(fill=tk.X, pady=(2, 2))
        row._vis_name = name
        row._callback = cb

        col = tk.Frame(row)
        col.pack(fill=tk.X)

        try:
            cls = get_visualizer(name)
            try:
                inst = cls()
                schema = inst.parameters() if hasattr(inst, 'parameters') else []
            except Exception:
                schema = getattr(cls, 'parameters', []) or []
        except Exception:
            schema = []

        if schema:
            params_frame = tk.Frame(col)
            params_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
            param_widgets, param_rows, param_labels = create_parameter_widgets(
                schema, params_frame, simulation_scripts
            )
            row._param_widgets = param_widgets
            row._param_rows = param_rows
            row._param_labels = param_labels
            param_getters[name] = create_parameter_getter(param_widgets)
        else:
            row._param_widgets = {}
            param_getters[name] = lambda: None

        btn = _make_button(name, cb, parent=col)
        row._button = btn

        try:
            div = tk.Frame(parent_for_name, height=1, bg='gray')
            div.pack(fill=tk.X, padx=6, pady=(0, 4))
            div._is_divider = True
        except Exception:
            pass

        return row

    def _inline_get_params(n):
        return param_getters.get(n, lambda: None)()

    make_visualizer_buttons(grouped_factory, get_params_fn=_inline_get_params, get_server_fn=gui_get_server)

    return frame


def run_gui():
    """Run the GUI as a standalone app."""
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
