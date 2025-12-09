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
        """Run visualization from 'data'. Must be overridden."""
        raise NotImplementedError()


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
