"""Runner registry for managing command execution backends.

This module provides a centralized registry for discovering and creating
runner instances. Runners are execution backends that handle shell commands
and file operations in different environments.
"""
import json
from typing import Dict, Type, Any, List, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from .runners.base import Runner


# Runner registry
_RUNNER_REGISTRY: Dict[str, Type['Runner']] = {}

# Runner instance storage (for named/configured runner instances)
_RUNNER_INSTANCES: Dict[str, 'Runner'] = {}

_runner_instances_loaded = False

def register_runner(cls: Type['Runner']):
    """Register a runner class for discovery.
    
    Args:
        cls: Runner class to register
        
    Returns:
        The registered class (for use as decorator)
    """
    name = getattr(cls, 'name', None) or cls.__name__.lower()
    _RUNNER_REGISTRY[name] = cls
    return cls


def list_runners() -> List[str]:
    """Return list of registered runner type names."""
    return sorted(_RUNNER_REGISTRY.keys())


def get_runner_class(name: str) -> Type['Runner']:
    """Get runner class by name.
    
    Args:
        name: Name of the runner type
        
    Returns:
        Runner class
        
    Raises:
        KeyError: If runner type not found
    """
    return _RUNNER_REGISTRY[name]


def create_runner(runner_type: str, config: Dict[str, Any] = None, instance_name: str = None) -> 'Runner':
    """Create a runner instance.
    
    Args:
        runner_type: Type name of the runner (e.g., 'local', 'ssh')
        config: Configuration for the runner
        instance_name: Optional name for storing this instance
        
    Returns:
        Runner instance
    """
    cls = get_runner_class(runner_type)
    runner = cls(config)
    
    if instance_name:
        _RUNNER_INSTANCES[instance_name] = runner
    
    return runner


def get_runner_instance(instance_name: str) -> 'Runner':
    """Get a named runner instance.
    
    Args:
        instance_name: Name of the runner instance
        
    Returns:
        Runner instance
        
    Raises:
        KeyError: If instance not found
    """
    if not _runner_instances_loaded:
        restore_runner_instances()
    return _RUNNER_INSTANCES[instance_name]


def list_runner_instances() -> List[str]:
    """Return list of configured runner instance names."""
    if not _runner_instances_loaded:
        restore_runner_instances()
    return sorted(_RUNNER_INSTANCES.keys())


def remove_runner_instance(instance_name: str) -> bool:
    """Remove a runner instance.
    
    Args:
        instance_name: Name of the runner instance
        
    Returns:
        True if removed, False if not found
    """
    if instance_name in _RUNNER_INSTANCES:
        runner = _RUNNER_INSTANCES[instance_name]
        # Clean up if runner has disconnect method
        if hasattr(runner, 'disconnect'):
            try:
                runner.disconnect()
            except Exception:
                pass
        del _RUNNER_INSTANCES[instance_name]
        return True
    return False


# Runner configuration persistence
RUNNERS_CONFIG_FILE = Path.home() / '.srw_ui_runners.json'


def load_runner_configs() -> Dict[str, Any]:
    """Load saved runner configurations from disk.
    
    Returns:
        Dictionary mapping instance_name -> config dict with 'type' and other settings
    """
    if not RUNNERS_CONFIG_FILE.exists():
        return {}
    try:
        with open(RUNNERS_CONFIG_FILE, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_runner_configs(configs: Dict[str, Any]) -> None:
    """Persist runner configurations to disk.
    
    Args:
        configs: Dictionary mapping instance_name -> config dict
    """
    try:
        with open(RUNNERS_CONFIG_FILE, 'w', encoding='utf-8') as fh:
            json.dump(configs, fh, indent=2)
    except Exception:
        pass


def restore_runner_instances() -> None:
    """Restore runner instances from saved configurations."""
    configs = load_runner_configs()
    for instance_name, config in configs.items():
        runner_type = config.get('type')
        if runner_type and runner_type in _RUNNER_REGISTRY:
            try:
                create_runner(runner_type, config, instance_name)
            except Exception:
                pass
    global _runner_instances_loaded
    _runner_instances_loaded = True

def save_runner_instance(instance_name: str, runner_type: str, config: Dict[str, Any]) -> None:
    """Save a runner instance configuration.
    
    Args:
        instance_name: Name for this runner instance
        runner_type: Type of runner
        config: Configuration dictionary
    """
    configs = load_runner_configs()
    configs[instance_name] = {
        'type': runner_type,
        **config
    }
    save_runner_configs(configs)
    
    # Create/update the instance
    create_runner(runner_type, config, instance_name)
