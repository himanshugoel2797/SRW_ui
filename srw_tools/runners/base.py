"""Base Runner class for command execution.

Runners handle execution of shell commands and file operations in
different environments (local, remote, containerized, etc.).
"""
from typing import Dict, Any, Optional, Tuple, List


class Runner:
    """Base class for command runners.
    
    Runners handle the execution of shell commands and file operations in
    different environments. Visualizers send commands and file requests to
    runners, which execute them in their specific context.
    """
    
    name: str = "base"
    display_name: str = "Base Runner"
    description: str = "Base runner class"
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the runner with optional configuration.
        
        Args:
            config: Configuration dictionary specific to this runner type
        """
        self.config = config or {}
    
    def run_command(self, command: str, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
        """Execute a shell command.
        
        Args:
            command: Shell command to execute
            cwd: Working directory for command execution
            env: Environment variables for the command
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError()
    
    def read_file(self, path: str) -> str:
        """Read contents of a file.
        
        Args:
            path: Path to the file to read
            
        Returns:
            File contents as string
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError()
    
    def write_file(self, path: str, content: str) -> bool:
        """Write content to a file.
        
        Args:
            path: Path to the file to write
            content: Content to write
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError()
    
    def list_files(self, path: str, pattern: Optional[str] = None) -> List[str]:
        """List files in a directory.
        
        Args:
            path: Directory path
            pattern: Optional glob pattern to filter files
            
        Returns:
            List of file paths
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError()
    
    def is_available(self) -> bool:
        """Check if this runner is currently available for use.
        
        Returns:
            True if the runner can be used, False otherwise
        """
        return True
    
    def get_config_schema(self) -> List[Dict[str, Any]]:
        """Return configuration parameters needed for this runner.
        
        Returns:
            List of parameter descriptors (similar to Visualizer.parameters())
            Each dict should have: name, type, label, default
        """
        return []
    
    def get_display_name(self) -> str:
        """Return human-friendly name for this runner."""
        return self.display_name or self.name.replace('_', ' ').title()
    
    def get_description(self) -> str:
        """Return description of this runner."""
        return self.description
