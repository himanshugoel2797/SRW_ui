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

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def run(self, data):
        """Compatibility wrapper for older visualizers.

        Prefer subclasses to implement `process(data)` for data-processing
        (server-side) logic. If `process` is implemented it will be used,
        otherwise we delegate to subclasses that override `run`.
        """
        # If the subclass overrides process, delegate to that to avoid
        # recursion between run/process defaults.
        if type(self).process is not Visualizer.process:
            return self.process(data)
        raise NotImplementedError()

    def process(self, data=None):
        """Process or generate visualization data.

        Implement this method to provide data processing logic that can run
        server-side. By default it delegates to `run` for backwards
        compatibility with older visualizers that implement `run`.
        """
        # If a server connection is attached to the instance, try to request
        # processed data transparently from the server. The expected server
        # API is `process_visualizer(name, params)` (XML-RPC friendly types).
        server = getattr(self, 'server', None)
        if server is not None:
            try:
                return server.process_visualizer(self.name, data or {})
            except Exception:
                # fall back to local processing on error
                pass

        if type(self).run is not Visualizer.run:
            return self.run(data)
        raise NotImplementedError()

    def view(self, parent=None, data=None):
        """Present the visualization in a UI.

        Prefer visualizers to implement `view(parent, data)` for UI-specific
        behaviour. By default this delegates to `show` for backward
        compatibility.
        """
        if type(self).show is not Visualizer.show:
            return self.show(parent=parent, data=data)
        raise NotImplementedError()

    def show(self, parent=None, data=None):
        """Compatibility wrapper that delegates to view() by default.

        Older visualizers may override `show` to attach windows; new-style
        visualizers should override `view` for UI behaviour and `process`
        for server-side data.
        """
        if type(self).view is not Visualizer.view:
            return self.view(parent=parent, data=data)
        # Fallback to run, which delegates to process if implemented.
        return self.run(data)

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
