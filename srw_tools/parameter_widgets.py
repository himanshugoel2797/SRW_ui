"""Parameter widgets for building visualizer UIs.

Provides reusable functions for creating tkinter parameter input widgets
based on parameter schemas from visualizers. Supports common types including
strings, numbers, booleans, files, directories, and simulations.
"""
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional, Tuple


def create_parameter_widgets(schema: List[Dict[str, Any]], parent, script_manager=None) -> Tuple[Dict[str, Tuple], List, Dict]:
    """Create parameter input widgets from a schema.

    Args:
        schema: List of parameter dicts with keys: name, type, default, label
        parent: tkinter parent widget
        script_manager: Optional script manager for simulation parameter type

    Returns:
        Tuple of (param_widgets, param_rows, param_labels) where:
        - param_widgets: dict mapping param name to (widget_or_var, type)
        - param_rows: list of frame widgets containing parameters
        - param_labels: dict mapping param name to label widgets
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return {}, [], {}

    param_widgets = {}
    param_rows = []
    param_labels = {}

    def _new_param_row():
        r = tk.Frame(parent)
        r.pack(fill=tk.X, anchor='w')
        param_rows.append(r)
        return r

    current_param_row = _new_param_row()

    for p in schema:
        pname = p['name']
        ptype = p.get('type')
        plabel_text = p.get('label') or pname

        if ptype == 'newline':
            current_param_row = _new_param_row()
            param_widgets[pname] = (None, 'newline')
            param_labels[pname] = None
            continue

        if ptype != 'bool':
            lab = tk.Label(current_param_row, text=plabel_text)
            lab.pack(side=tk.LEFT, padx=(2, 2))
            param_labels[pname] = lab

        if ptype == 'bool':
            var = tk.BooleanVar(value=bool(p.get('default')))
            cbw = tk.Checkbutton(current_param_row, text=plabel_text, variable=var)
            cbw.pack(side=tk.LEFT, padx=(4, 2))
            param_widgets[pname] = (var, 'bool')

        elif ptype == 'simulation':
            widget, var = _create_simulation_widget(p, current_param_row, script_manager)
            param_widgets[pname] = (var, 'simulation')

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
            param_widgets[pname] = (sval, ptype)

        else:
            ent = tk.Entry(current_param_row, width=12)
            default = p.get('default')
            if default is not None:
                ent.insert(0, str(default))
            ent.pack(side=tk.LEFT, padx=(4, 2))
            param_widgets[pname] = (ent, ptype or 'str')

    return param_widgets, param_rows, param_labels


def _create_simulation_widget(param_spec: Dict[str, Any], parent, script_manager):
    """Create an OptionMenu for selecting simulation scripts."""
    import tkinter as tk

    try:
        sims = script_manager.list_simulation_scripts() if script_manager else {}
    except Exception:
        sims = {}

    paths = sorted(sims.keys())
    default = param_spec.get('default') or ''
    selected_path = ''

    if default in paths:
        selected_path = default
    else:
        for path, _name in sims.items():
            if _name == default:
                selected_path = path
                break
    if not selected_path and paths:
        selected_path = paths[0]

    value_var = tk.StringVar(value=selected_path)
    display_var = tk.StringVar(value=(f"{sims.get(selected_path) or ''} - {Path(selected_path).name}" if selected_path else ''))

    if paths:
        opt = tk.OptionMenu(parent, display_var, *[f"{sims.get(p) or ''} - {Path(p).name}" for p in paths])
        try:
            menu = opt['menu']
            menu.delete(0, 'end')
            for path in paths:
                label = sims.get(path) or ''
                display = f"{label} - {Path(path).name}" if label else Path(path).name

                def _make_cmd(p=path, d=display):
                    def _cmd():
                        display_var.set(d)
                        value_var.set(p)
                    return _cmd

                menu.add_command(label=display, command=_make_cmd())
        except Exception:
            pass
        opt.pack(side=tk.LEFT, padx=(4, 2))
    else:
        lbl = tk.Label(parent, text='(no sims)')
        lbl.pack(side=tk.LEFT, padx=(4, 2))

    return opt, value_var


def create_parameter_getter(param_widgets: Dict[str, Tuple]) -> Callable[[], Dict[str, Any]]:
    """Create a function that extracts current parameter values from widgets.

    Args:
        param_widgets: Dict mapping param name to (widget_or_var, type)

    Returns:
        Callable that returns dict of current parameter values
    """
    def _getter():
        vals = {}
        for k, w in param_widgets.items():
            widget, ptype = w
            if ptype == 'newline':
                continue
            try:
                raw = widget.get()
            except Exception:
                raw = None

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

    return _getter
