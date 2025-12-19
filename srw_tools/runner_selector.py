"""GUI helper for runner selection widgets.

Provides a small tkinter widget factory to select a named runner instance
and a helper to obtain the selected runner instance lazily.
"""


def create_runner_selector(parent, initial_instance=None, include_none=True):
    try:
        import tkinter as tk
    except Exception:
        def _noop_get():
            return None
        return None, _noop_get

    from .runner_registry import (
        list_runner_instances, load_runner_configs, get_runner_instance, create_runner
    )

    frame = tk.Frame(parent)
    tk.Label(frame, text='Runner:').pack(side=tk.LEFT, padx=(0, 6))

    instances = list_runner_instances()
    if include_none:
        opts = ['<None>'] + instances
    else:
        opts = instances or ['']

    selected = tk.StringVar()
    if initial_instance and initial_instance in instances:
        selected.set(initial_instance)
    else:
        selected.set(opts[0] if opts else '')

    menu = tk.OptionMenu(frame, selected, *opts)
    menu.pack(side=tk.LEFT)

    def get_selected_runner():
        name = selected.get()
        if include_none and name == '<None>':
            return None

        try:
            return get_runner_instance(name)
        except Exception:
            try:
                configs = load_runner_configs()
                config = configs.get(name, {})
                rtype = config.get('type')
                if rtype:
                    try:
                        return create_runner(rtype, config, name)
                    except Exception:
                        return None
            except Exception:
                return None

        return None

    return frame, get_selected_runner
