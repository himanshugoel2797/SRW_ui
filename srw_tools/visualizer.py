"""Base visualizer class and registry for UI scripts.

Keep things tiny: a Visualizer base class and a registry that scripts
can use to register themselves for discovery by the CLI.
"""
from typing import Dict, Type, Any


class Visualizer:
    """Base class for simple visualizers.

    Subclasses should implement 'name' and 'run' at minimum. Keeping an
    abstract base is lightweight to make tests and extensions easy.
    """

    name: str = "base"
    # Optional human-friendly label used by GUIs. If None, the UI should
    # fall back to a title-cased version of `name` (e.g. 'my_vis' -> 'My Vis').
    display_name: str = None
    # Optional grouping key used by UIs to group visualizers. Subclasses can
    # set this to categorize similar visualizers (e.g. 'Math', 'Images').
    group: str = None

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    # Visualizers should implement `local_process` for data processing
    # and `view` for UI behaviour. The public `process` method handles
    # optional remote execution and then calls the local implementation.

    def process(self, data=None):
        """Process or generate visualization data.

        This method supports optional remote execution when a `server`
        dict with an active SSH connection (`_conn`) and `remote_cmd` is
        attached to the visualizer instance.
        
        TODO: Review remote execution implementation for security and error handling.
        """
        server = getattr(self, 'server', None)
        if isinstance(server, dict):
            conn = server.get('_conn')
            remote_cmd = server.get('remote_cmd')
            if conn and remote_cmd:
                try:
                    import json
                    from .ssh_helper import run_command
                    payload = json.dumps(data or {})
                    cmd = remote_cmd.format(name=self.name, params=payload)
                    status, out, err = run_command(conn, cmd)
                    if status == 0:
                        try:
                            return json.loads(out)
                        except Exception:
                            return out
                except Exception:
                    pass

        return self.local_process(data)

    def local_process(self, data=None):
        """Process or generate visualization data (local implementation).

        Subclasses must implement this method to provide local processing
        logic. The base `process` will call this when remote execution is
        not used or fails.
        """
        raise NotImplementedError()

    def view(self, data=None):
        """Present the visualization in a UI.

        Subclasses should implement `view(data)` for UI-specific behaviour.
        Visualizers are responsible for creating windows or returning processed
        data when called in non-GUI contexts.
        
        TODO: Consider standardizing the return value contract for headless vs GUI usage.
        """
        raise NotImplementedError()

    def parameters(self):
        """Return a list of parameter descriptors describing what inputs
        this visualizer accepts. Each descriptor is a dict with keys:
            - name: parameter key
            - type: 'int'|'float'|'str'|'bool'
            - default: a default value
            - label: optional display label

        Defaults to an empty list (no parameters).
        """
        return []

    def get_display_name(self):
        """Return a human friendly name for this visualizer.

        Uses explicit `display_name` if provided by subclasses; otherwise
        creates a readable form from the internal `name`.
        """
        if self.display_name:
            return self.display_name
        # default: turn snake-case or simple names into Title Case
        n = getattr(self, 'name', None) or self.__class__.__name__
        return n.replace('_', ' ').title()

    def get_group(self):
        """Return a group name for this visualizer for UI grouping.

        If `group` is provided by the subclass, return that. Otherwise
        return a sensible default 'Other'.
        """
        if getattr(self, 'group', None):
            return self.group
        return 'Other'


# simple registry so tools can discover visualizers by name
_REGISTRY: Dict[str, Type[Visualizer]] = {}


def register_visualizer(cls: Type[Visualizer]):
    """Decorator / function to register a Visualizer subclass."""
    name = getattr(cls, 'name', None) or cls.__name__.lower()
    _REGISTRY[name] = cls
    return cls


def list_visualizers():
    return sorted(_REGISTRY.keys())


def get_visualizer(name: str) -> Type[Visualizer]:
    return _REGISTRY[name]
