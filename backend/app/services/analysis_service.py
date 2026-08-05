"""Repository-wide Java parsing orchestration."""

import logging
from pathlib import Path

from app.exceptions.repository import (
    InvalidRepositoryPathError,
    JavaParsingError,
    RepositoryAnalysisError,
)
from app.schemas.repositories import RepositoryAnalyzeResponse
from app.services.java_parser_service import JavaParserService

logger = logging.getLogger(__name__)


class AnalysisService:
    """Discover and parse Java files in a cloned repository."""

    def __init__(self, java_parser_service: JavaParserService) -> None:
        self._java_parser_service = java_parser_service

    def analyze_repository(self, local_path: str | Path) -> RepositoryAnalyzeResponse:
        """Parse every Java file and return aggregate parsing counts."""
        repository_path = self._resolve_repository_path(local_path)
        try:
            java_files = tuple(self._java_files(repository_path))
        except OSError as error:
            logger.exception(
                "Java file discovery failed",
                extra={"local_path": repository_path},
            )
            raise RepositoryAnalysisError("Unable to discover Java source files.") from error

        parsed_successfully = 0
        parse_failures = 0
        for java_file in java_files:
            try:
                self._java_parser_service.parse_file(java_file)
                parsed_successfully += 1
            except JavaParsingError as error:
                parse_failures += 1
                parser_error = error.__cause__ or error
                logger.error(
                    "Java source file could not be parsed",
                    extra={
                        "file_path": java_file,
                        "exception_type": getattr(
                            parser_error,
                            "exception_type",
                            type(parser_error).__name__,
                        ),
                        "exception_message": self._error_message(parser_error),
                    },
                    exc_info=(
                        type(parser_error),
                        parser_error,
                        parser_error.__traceback__,
                    ),
                )

        response = RepositoryAnalyzeResponse(
            total_java_files=len(java_files),
            parsed_successfully=parsed_successfully,
            parse_failures=parse_failures,
        )
        logger.info(
            "Repository Java parsing analysis completed",
            extra={
                "local_path": repository_path,
                "total_java_files": response.total_java_files,
                "parsed_successfully": response.parsed_successfully,
                "parse_failures": response.parse_failures,
            },
        )
        return response

    @staticmethod
    def _resolve_repository_path(local_path: str | Path) -> Path:
        """Resolve and validate the repository directory to analyze."""
        repository_path = Path(local_path).expanduser().resolve()
        if not repository_path.is_dir():
            raise InvalidRepositoryPathError(
                "Repository path must exist and reference a directory."
            )
        return repository_path

    @staticmethod
    def _java_files(repository_path: Path) -> list[Path]:
        """Recursively discover Java source files outside Git metadata."""
        return [
            path
            for path in repository_path.rglob("*.java")
            if ".git" not in path.relative_to(repository_path).parts
        ]

    @staticmethod
    def _error_message(error: Exception) -> str:
        """Return the parser's descriptive message when one is available."""
        return str(error) or str(getattr(error, "description", "")) or repr(error)
