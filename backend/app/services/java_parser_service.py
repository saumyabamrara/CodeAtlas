"""Java source parsing through the JavaParser engine."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.exceptions.repository import InvalidJavaSourceFileError, JavaParsingError


@dataclass(frozen=True)
class JavaParserResult:
    """Parser representation for a successfully parsed Java compilation unit."""

    file_path: Path


class JavaParserEngineError(RuntimeError):
    """Error details reported by the JavaParser bridge process."""

    def __init__(self, exception_type: str, exception_message: str) -> None:
        super().__init__(exception_message)
        self.exception_type = exception_type


class JavaParserService:
    """Parse one Java source file with the JavaParser Java library."""

    def __init__(self, runner_jar: Path, java_executable: str = "java") -> None:
        self._runner_jar = runner_jar.expanduser().resolve()
        self._java_executable = java_executable

    def parse_file(self, file_path: str | Path) -> JavaParserResult:
        """Validate and parse a single Java source file."""
        source_path = Path(file_path).expanduser().resolve()
        if source_path.suffix.lower() != ".java" or not source_path.is_file():
            raise InvalidJavaSourceFileError(
                "File path must exist and reference a Java source file."
            )
        if not self._runner_jar.is_file():
            raise JavaParsingError(
                "JavaParser runner JAR is unavailable. Build backend/java_parser first."
            )

        try:
            completed_process = subprocess.run(
                [self._java_executable, "-jar", str(self._runner_jar), str(source_path)],
                capture_output=True,
                check=False,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise JavaParsingError(
                f"Unable to start JavaParser for {source_path.name}."
            ) from error

        if completed_process.returncode != 0:
            engine_error = self._engine_error(completed_process.stderr)
            raise JavaParsingError(
                f"Unable to parse Java source file: {source_path.name}."
            ) from engine_error
        return JavaParserResult(file_path=source_path)

    @staticmethod
    def _engine_error(error_output: str) -> JavaParserEngineError:
        """Convert structured bridge error output into a Python exception."""
        exception_type, separator, exception_message = error_output.strip().partition("|")
        if separator:
            return JavaParserEngineError(exception_type, exception_message)
        return JavaParserEngineError("JavaParserProcessError", error_output.strip())
