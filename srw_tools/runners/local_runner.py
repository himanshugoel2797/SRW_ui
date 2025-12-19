"""Local runner for executing commands on the current machine."""
import subprocess
import os
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from glob import glob

from .base import Runner
from ..runner_registry import register_runner


@register_runner
class LocalRunner(Runner):
    """Runner that executes commands locally on the current machine."""
    
    name = "local"
    display_name = "Local"
    description = "Execute commands on the local machine"
    
    def run_command(self, command: str, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
        """Execute command locally using subprocess.
        
        Args:
            command: Shell command to execute
            cwd: Working directory for command execution
            env: Environment variables for the command
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Merge environment with current environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env=exec_env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 300 seconds"
        except Exception as e:
            return -1, "", str(e)
    
    def read_file(self, path: str) -> str:
        """Read file from local filesystem.
        
        Args:
            path: Path to the file to read
            
        Returns:
            File contents as string
        """
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, path: str, content: str) -> bool:
        """Write file to local filesystem.
        
        Args:
            path: Path to the file to write
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directories if needed
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def list_files(self, path: str, pattern: Optional[str] = None) -> List[str]:
        """List files in local directory.
        
        Args:
            path: Directory path
            pattern: Optional glob pattern to filter files
            
        Returns:
            List of file paths
        """
        p = Path(path)
        
        if not p.exists() or not p.is_dir():
            return []
        
        if pattern:
            search_path = str(p / pattern)
            return sorted(glob(search_path))
        else:
            return sorted([str(f) for f in p.iterdir()])
