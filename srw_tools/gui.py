"""Small tkinter GUI that lists registered visualizers as buttons.

Design goals:
- Provide a test-friendly factory function `make_visualizer_buttons` that
  doesn't require tkinter so tests can verify behavior in headless CI.
- Provide `build_frame(parent)` which wires those buttons into a tkinter Frame.
- Provide `run_gui()` entry which runs a small app.
"""
from typing import Callable


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
    servers = {}  # mapping url -> proxy
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
            import xmlrpc.client

            proxy = xmlrpc.client.ServerProxy(url)
            servers[url] = proxy
            # update menu
            menu = server_menu['menu']
            menu.add_command(label=url, command=tk._setit(selected_server, url))
            selected_server.set(url)
        except Exception as e:
            messagebox.showerror('Server error', str(e))

    add_button = tk.Button(server_frame, text='Add server', command=add_server)
    add_button.pack(side=tk.LEFT, padx=(0, 4))

    server_menu = tk.OptionMenu(server_frame, selected_server, '')
    server_menu.pack(side=tk.LEFT)

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
