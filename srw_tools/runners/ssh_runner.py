"""SSH runner for executing commands on remote servers."""
import asyncio
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import shlex

from .base import Runner
from ..runner_registry import register_runner


@register_runner
class SSHRunner(Runner):
    """Runner that executes commands on a remote SSH server."""
    
    name = "ssh"
    display_name = "SSH Remote"
    description = "Execute commands on a remote server via SSH"
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize SSH runner with connection details.
        
        Args:
            config: Must include 'url', optionally 'path', 'conda_env', etc.
        """
        super().__init__(config)
        self._conn = None
        self._listener = None
    
    def run_command(self, command: str, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
        """Execute command on remote SSH server.
        
        Args:
            command: Shell command to execute
            cwd: Working directory for command execution
            env: Environment variables for the command
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
            
        Raises:
            RuntimeError: If not connected
        """
        if not self._conn:
            raise RuntimeError("SSH runner not connected. Call connect() first.")
        
        try:
            from ..ssh_helper import run_command as ssh_run_command
            
            # Build the full command with environment and cwd
            full_cmd = []
            
            # Add conda activation if configured
            conda_env = self.config.get('conda_env')
            if conda_env:
                full_cmd.append(f"conda activate {conda_env}")
            
            # Add environment variables
            if env:
                env_str = ' '.join([f"{k}={v}" for k, v in env.items()])
                full_cmd.append(env_str)
            
            # Add working directory change
            if cwd:
                full_cmd.append(f"cd {cwd}")
            elif self.config.get('path'):
                full_cmd.append(f"cd {self.config['path']}")
            
            # Add the actual command
            full_cmd.append(command)
            
            # Join with && to ensure all steps succeed
            final_cmd = ' && '.join(full_cmd)
            
            status, out, err = ssh_run_command(self._conn, final_cmd)
            return status, out, err
        except Exception as e:
            return -1, "", str(e)
    
    def read_file(self, path: str) -> str:
        """Read file from remote server.
        
        Args:
            path: Path to the file on remote server
            
        Returns:
            File contents as string
            
        Raises:
            RuntimeError: If not connected
        """
        if not self._conn:
            raise RuntimeError("SSH runner not connected. Call connect() first.")
        
        try:
            from ..ssh_helper import run_command as ssh_run_command
            status, out, err = ssh_run_command(self._conn, f"cat {path}")
            if status == 0:
                return out
            else:
                raise IOError(f"Failed to read file: {err}")
        except Exception as e:
            raise IOError(f"Error reading remote file: {e}")
    
    def write_file(self, path: str, content: str) -> bool:
        """Write file to remote server.
        
        Args:
            path: Path to the file on remote server
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        if not self._conn:
            return False
        
        try:
            from ..ssh_helper import run_command as ssh_run_command
            
            # Create parent directory if needed
            parent_dir = str(Path(path).parent)
            ssh_run_command(self._conn, f"mkdir -p {parent_dir}")
            
            # Write content using echo (escape for shell)
            escaped_content = shlex.quote(content)
            status, _, _ = ssh_run_command(self._conn, f"echo {escaped_content} > {path}")
            
            return status == 0
        except Exception:
            return False
    
    def list_files(self, path: str, pattern: Optional[str] = None) -> List[str]:
        """List files in remote directory.
        
        Args:
            path: Directory path on remote server
            pattern: Optional glob pattern to filter files
            
        Returns:
            List of file paths
            
        Raises:
            RuntimeError: If not connected
        """
        if not self._conn:
            raise RuntimeError("SSH runner not connected. Call connect() first.")
        
        try:
            from ..ssh_helper import run_command as ssh_run_command
            
            if pattern:
                cmd = f"ls -1 {path}/{pattern} 2>/dev/null"
            else:
                cmd = f"ls -1 {path} 2>/dev/null"
            
            status, out, _ = ssh_run_command(self._conn, cmd)
            
            if status == 0 and out.strip():
                return sorted([line.strip() for line in out.strip().split('\n') if line.strip()])
            return []
        except Exception:
            return []
    
    def is_available(self) -> bool:
        """Check if SSH connection is active."""
        return self._conn is not None
    
    def get_config_schema(self) -> List[Dict[str, Any]]:
        """Return SSH connection configuration parameters."""
        return [
            {'name': 'url', 'type': 'str', 'label': 'SSH Target (user@host)', 'default': ''},
            {'name': 'path', 'type': 'str', 'label': 'Remote Path', 'default': ''},
            {'name': 'conda_env', 'type': 'str', 'label': 'Conda Environment', 'default': ''},
        ]
    
    def connect(self) -> Tuple[bool, str]:
        """Establish SSH connection.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        url = self.config.get('url')
        if not url:
            return False, "No URL configured"
        
        try:
            from ..ssh_helper import connect_sync
            self._conn = connect_sync(url)
            return True, f"Connected to {url}"
        except Exception as e:
            return False, str(e)
    
    def disconnect(self) -> Tuple[bool, str]:
        """Close SSH connection.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self._listener and hasattr(self._listener, 'close'):
            try:
                self._listener.close()
            except Exception:
                pass
        
        if self._conn:
            try:
                c = self._conn.close()
                if asyncio.iscoroutine(c):
                    loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(c)
                    finally:
                        try:
                            asyncio.set_event_loop(None)
                        except Exception:
                            pass
            except Exception:
                pass
        
        self._conn = None
        self._listener = None
        return True, "Disconnected"
