class ValisWorkstationError(Exception):
    """Base exception for VALIS Workstation errors."""


class UserVisibleError(ValisWorkstationError):
    """Errors that should be shown to the user in the GUI."""
