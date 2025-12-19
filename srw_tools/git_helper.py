# git_helper removed — importing this module is an error.
#
# The project no longer supports git-based backups. If code still
# imports `srw_tools.git_helper` the import will now raise ImportError
# with a message directing users to the new ZIP-based backup flow.

raise ImportError(
    "srw_tools.git_helper has been removed. Use local archive backups\n"
    "(e.g., the Simulation Data Manager 'Backup (zip)') or external git tooling."
)
