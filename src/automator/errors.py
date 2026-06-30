class AutomationError(Exception):
    """Expected automation failure with a user-facing message (no stack trace in logs)."""


class RepositoryNotFoundError(AutomationError):
    """GitHub repository does not exist yet — caller should create it and retry."""
