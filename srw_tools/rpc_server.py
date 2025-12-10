"""Simple RPC server for running small commands and file helpers.

This uses Python's built-in xmlrpc server and exposes tiny helper
functions for remote invocation. Keep the API minimal and easy to extend.
"""
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xmlrpc.client
import threading
import time
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
        # client registration for callbacks
        self.server.register_function(self.register_client)
        self.server.register_function(self.unregister_client)
        self.server.register_function(self.list_clients)
        self._clients = {}  # client_id -> client_info dict {url, last_seen}

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

    def register_client(self, client_id: str, client_url: str):
        """Register a remote client URL for callbacks.

        client_id: an opaque identifier supplied by the client (e.g. UUID)
        client_url: RPC URL where the client is reachable (e.g. http://host:port/)
        Returns True on success.
        """
        try:
            # validate by making a minimal RPC call
            proxy = xmlrpc.client.ServerProxy(client_url)
            # ping method may not exist; it's okay if the call raises -- we'll accept
            self._clients[client_id] = {'url': client_url, 'last_seen': time.time()}
            return True
        except Exception:
            return False

    def unregister_client(self, client_id: str):
        if client_id in self._clients:
            del self._clients[client_id]
            return True
        return False

    def list_clients(self):
        return list(self._clients.keys())

    def _call_client(self, client_url: str, method: str, *args):
        try:
            proxy = xmlrpc.client.ServerProxy(client_url)
            fn = getattr(proxy, method)
            return fn(*args)
        except Exception:
            return None

    def process_visualizer(self, name: str, params: dict, client_url: str = None, client_id: str = None):
        """Run a visualizer's process(name, params) on the server and return the result.

        This allows remote clients to request processed data from the server.
        """
        try:
            # avoid importing heavy modules at top-level
            from srw_tools.visualizer import get_visualizer

            cls = get_visualizer(name)
            inst = cls()
            result = inst.process(params)
            # If a client_url or client_id is provided, attempt to call back
            cb = None
            if client_url:
                cb = client_url
            elif client_id and client_id in self._clients:
                cb = self._clients[client_id]['url']

            if cb:
                # call a `on_visualizer_result(name, result)` method on the client
                # do it asynchronously so the RPC call completes quickly
                def _async_cb(url, n, r):
                    try:
                        self._call_client(url, 'on_visualizer_result', n, r)
                    except Exception:
                        pass

                t = threading.Thread(target=_async_cb, args=(cb, name, result), daemon=True)
                t.start()
                # return an acknowledgement to the caller
                return True

            return result
        except Exception as e:
            # XML-RPC will return a fault for exceptions; keep the error simple
            raise
