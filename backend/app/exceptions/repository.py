"""Exceptions raised during repository ingestion."""


class InvalidRepositoryUrlError(ValueError):
    """Raised when a repository URL is not a supported public GitHub URL."""


class RepositoryCloneError(RuntimeError):
    """Raised when a repository cannot be cloned."""
