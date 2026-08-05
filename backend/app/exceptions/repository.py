"""Exceptions raised during repository ingestion."""


class InvalidRepositoryUrlError(ValueError):
    """Raised when a repository URL is not a supported public GitHub URL."""


class RepositoryCloneError(RuntimeError):
    """Raised when a repository cannot be cloned."""


class InvalidRepositoryPathError(ValueError):
    """Raised when a repository inspection path does not exist or is not a directory."""


class RepositoryInspectionError(RuntimeError):
    """Raised when repository metadata cannot be inspected."""


class InvalidJavaSourceFileError(ValueError):
    """Raised when a requested file is not a Java source file."""


class JavaParsingError(RuntimeError):
    """Raised when a Java source file cannot be parsed."""


class RepositoryAnalysisError(RuntimeError):
    """Raised when Java file discovery for repository analysis fails."""
