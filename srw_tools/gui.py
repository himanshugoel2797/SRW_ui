"""Small tkinter GUI that lists registered visualizers as buttons.

Provides a test-friendly factory function `make_visualizer_buttons` and
integration with command runners for executing visualizations.
"""
from typing import Callable

from .parameter_widgets import create_parameter_widgets, create_parameter_getter
from . import simulation_scripts


def make_visualizer_buttons(create_button_fn: Callable[[str, Callable], object], *, get_params_fn=None, get_runner_fn=None):
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

                if callable(get_runner_fn):
                    try:
                        inst.runner = get_runner_fn(n)
                    except Exception:
                        inst.runner = None

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
        from tkinter import messagebox, filedialog, simpledialog
        import asyncio
    except Exception as e:
        raise RuntimeError('tkinter not available') from e

    # Runner management moved to separate visualizer/registry; GUI no longer
    # manages runner instances or connections.

    frame = tk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True)

    # Runner management moved out of GUI (handled by runner manager visualizer)

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

    # Runner UI removed: runner selection and management moved to
    # the Runner Manager visualizer (`runner_config_visualizer.py`).

    # Create grouped sections for visualizers so the UI is easier to
    # navigate when many visualizers are available.
    # We'll map visualizer name -> group and create a frame per group.
    from .visualizer import list_visualizers, get_visualizer

    name_to_group = {}
    groups = {}
    # Determine per-group default collapsed state: if any visualizer class
    # in the group declares `group_collapsed = True` or its instance
    # `get_group_default_collapsed()` returns True, the group will start
    # collapsed.
    group_default_collapsed = {}

    for name in list_visualizers():
        try:
            cls = get_visualizer(name)
            try:
                inst = cls()
                grp = inst.get_group() if hasattr(inst, 'get_group') else getattr(cls, 'group', None) or 'Other'
                # check class attribute first
                default_collapsed = getattr(cls, 'group_collapsed', False)
                # instance-level override if provided
                if not default_collapsed and hasattr(inst, 'get_group_default_collapsed'):
                    try:
                        default_collapsed = bool(inst.get_group_default_collapsed())
                    except Exception:
                        default_collapsed = default_collapsed
            except Exception:
                grp = getattr(cls, 'group', None) or 'Other'
                default_collapsed = getattr(cls, 'group_collapsed', False)
        except Exception:
            grp = 'Other'
            default_collapsed = False

        name_to_group[name] = grp
        groups.setdefault(grp, []).append(name)
        # record default collapsed if any visualizer marks it
        if default_collapsed:
            group_default_collapsed[grp] = True

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
    # container for inline (parameter-less) buttons per group
    group_inline_frames = {}
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

        # inline container for parameter-less visualizer buttons
        inline = tk.Frame(gf)
        inline.pack(fill=tk.X, padx=(0, 0), pady=(2, 2))
        group_inline_frames[grp] = inline

        group_frames[grp] = gf
        # add a group divider below this group's content for visual separation
        try:
            gdiv = tk.Frame(groups_container, height=2, bg='black')
            gdiv.pack(fill=tk.X, padx=4, pady=(2, 6))
            gdiv._is_group_divider = True
        except Exception:
            pass
        group_buttons[grp] = btn
        # initialize collapsed state from discovered defaults
        group_collapsed[grp] = bool(group_default_collapsed.get(grp, False))
        if group_collapsed[grp]:
            # start collapsed
            gf.pack_forget()
            btn.config(text='+')

    param_getters = {}

    def grouped_factory(name, cb):
        grp = name_to_group.get(name, 'Other')
        parent_for_name = group_frames.get(grp)

        try:
            cls = get_visualizer(name)
            try:
                inst = cls()
                schema = inst.parameters() if hasattr(inst, 'parameters') else []
            except Exception:
                schema = getattr(cls, 'parameters', []) or []
        except Exception:
            schema = []

        # If the visualizer has no parameters, place its button inline
        # in the group's inline container so multiple simple visualizers
        # appear on the same row.
        if not schema:
            row = tk.Frame(group_inline_frames.get(grp))
            row.pack(side=tk.LEFT, padx=(2, 2), pady=(2, 2))
            row._vis_name = name
            row._callback = cb
            row._param_widgets = {}
            param_getters[name] = lambda: None

            btn = _make_button(name, cb, parent=row)
            row._button = btn
            return row

        # Visualizers with parameters get a full-width row
        row = tk.Frame(parent_for_name)
        row.pack(fill=tk.X, pady=(2, 2))
        row._vis_name = name
        row._callback = cb

        col = tk.Frame(row)
        col.pack(fill=tk.X)

        params_frame = tk.Frame(col)
        params_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        param_widgets, param_rows, param_labels = create_parameter_widgets(
            schema, params_frame, simulation_scripts
        )
        row._param_widgets = param_widgets
        row._param_rows = param_rows
        row._param_labels = param_labels
        param_getters[name] = create_parameter_getter(param_widgets)

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

    # GUI no longer provides runners to visualizers; visualizers that need
    # runners should request them via their own UI flow (runner manager).
    make_visualizer_buttons(grouped_factory, get_params_fn=_inline_get_params)

    # Runner status is managed by runner implementations/manager visualizer.

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
