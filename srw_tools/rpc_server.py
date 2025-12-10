"""RPC server support removed.

This module used to provide a tiny XML-RPC server. The project no longer
supports RPC-based workflows; SSH helpers should be used instead. Importing
this module will raise an ImportError to make missing references obvious.
"""

raise ImportError("srw_tools.rpc_server has been removed. Use srw_tools.ssh_helper instead.")
