"""Simple RPC server for running small commands and file helpers.

This uses Python's built-in xmlrpc server and exposes tiny helper
functions for remote invocation. Keep the API minimal and easy to extend.
"""
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import subprocess
import os
from typing import Optional, Iterable


class RPCRequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class RPCServer:
    """A small wrapper around SimpleXMLRPCServer.

    Methods exposed (by default):
      - execute_command(cmd: str) -> (exitcode:int, stdout:str, stderr:str)
      - list_files(path: str) -> list[str]
      - read_file(path: str) -> str
      - write_file(path: str, content: str) -> bool

    For safety, restrict file operations to the allowed_dirs if provided.
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 0, allowed_dirs: Optional[Iterable[str]] = None):
        self.server = SimpleXMLRPCServer((host, port), requestHandler=RPCRequestHandler, allow_none=True)
        self.server.register_introspection_functions()
        self.allowed_dirs = [os.path.abspath(d) for d in allowed_dirs] if allowed_dirs else None
        # register methods
        self.server.register_function(self.execute_command)
        self.server.register_function(self.list_files)
        self.server.register_function(self.read_file)
        self.server.register_function(self.write_file)
        # register visualizer processing helper so remote clients can ask the
        # server to run a visualizer's process() on the server-side.
        self.server.register_function(self.process_visualizer)

    def _is_allowed_path(self, path: str) -> bool:
        """Check the absolute path is inside one of allowed_dirs or allow all if None."""
        if self.allowed_dirs is None:
            return True
        abspath = os.path.abspath(path)
        return any(os.path.commonpath([abspath, d]) == d for d in self.allowed_dirs)

    def execute_command(self, cmd: str):
        """Run a shell command and return (code, stdout, stderr)."""
        try:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return proc.returncode, proc.stdout, proc.stderr
        except Exception as e:
            return -1, '', str(e)

    def list_files(self, path: str = '.'):
        if not self._is_allowed_path(path):
            raise PermissionError('path not allowed')
        try:
            return sorted(os.listdir(path))
        except Exception as e:
            return []

    def read_file(self, path: str):
        if not self._is_allowed_path(path):
            raise PermissionError('path not allowed')
        with open(path, 'r', encoding='utf-8') as fh:
            return fh.read()

    def write_file(self, path: str, content: str):
        if not self._is_allowed_path(path):
            raise PermissionError('path not allowed')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(content)
        return True

    def serve_forever(self):
        print(f"Starting RPC server on {self.server.server_address}")
        self.server.serve_forever()

    def process_visualizer(self, name: str, params: dict):
        """Run a visualizer's process(name, params) on the server and return the result.

        This allows remote clients to request processed data from the server.
        """
        try:
            # avoid importing heavy modules at top-level
            from srw_tools.visualizer import get_visualizer

            cls = get_visualizer(name)
            inst = cls()
            return inst.process(params)
        except Exception as e:
            # XML-RPC will return a fault for exceptions; keep the error simple
            raise
