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
    # transparent RPC delegation and then calls the local implementation.

    def process(self, data=None):
        """Process or generate visualization data.

        This method handles transparent RPC delegation. Subclasses should
        implement `local_process` instead of overriding this method.
        """
        # If a server connection is attached to the instance, try to request
        # processed data transparently from the server. The expected server
        # API is `process_visualizer(name, params)` (XML-RPC friendly types).
        server = getattr(self, 'server', None)
        # Support `server` being either a dict containing 'local_proxy'
        # and callback metadata (as used by the GUI) or an xmlrpc proxy.
        if isinstance(server, dict):
            try:
                import xmlrpc.client
                server_info = server
                local_proxy = server_info.get('local_proxy') or server_info.get('client_url')
                if local_proxy:
                    server = xmlrpc.client.ServerProxy(local_proxy)
                    # cache proxy for subsequent calls
                    self.server = server
                # expose callback info to this visualizer instance
                self.client_url = server_info.get('callback_url')
                self.client_id = server_info.get('callback_id')
            except Exception:
                pass
        if server is not None:
            try:
                # If a client_url or client_id was configured on this instance, pass it to
                # the server so the server can perform callback notifications.
                client_url = getattr(self, 'client_url', None)
                client_id = getattr(self, 'client_id', None)
                if client_url is not None:
                    return server.process_visualizer(self.name, data or {}, client_url)
                if client_id is not None:
                    # XML-RPC doesn't support keyword args, pass None for client_url
                    return server.process_visualizer(self.name, data or {}, None, client_id)
                # default / backward compatible
                return server.process_visualizer(self.name, data or {})
            except Exception:
                # fall back to local processing on error
                pass

        return self.local_process(data)

    def local_process(self, data=None):
        """Process or generate visualization data (local implementation).

        Subclasses must implement this method to provide local processing
        logic. The base `process` handles any RPC delegation and then calls
        into this method when running locally.
        """
        raise NotImplementedError()

    def view(self, data=None):
        """Present the visualization in a UI.

        Subclasses should implement `view(data)` for UI-specific behaviour.
        The GUI will only pass the parameter dictionary to visualizers and
        visualizers are responsible for creating windows or returning processed
        data. When called in non-GUI contexts visualizers may return processed
        data.
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
