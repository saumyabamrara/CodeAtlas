"""Filesystem-based repository metadata inspection."""

import logging
import re
from pathlib import Path

from app.exceptions.repository import (
    InvalidRepositoryPathError,
    RepositoryInspectionError,
)
from app.schemas.repositories import RepositoryInspectResponse

logger = logging.getLogger(__name__)

_SPRING_BOOT_APPLICATION_PATTERN = re.compile(
    r"@(?:[A-Za-z_]\w*\.)*SpringBootApplication\b"
)
_PACKAGE_PATTERN = re.compile(r"\bpackage\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*;")
_CLASS_PATTERN = re.compile(r"\bclass\s+([A-Za-z_]\w*)\b")
_GIT_ORIGIN_URL_PATTERN = re.compile(
    r'^\s*url\s*=\s*(.+?)\s*$',
    re.MULTILINE,
)


class RepositoryInspector:
    """Inspect a cloned repository without parsing its source code into an AST."""

    def inspect_repository(self, local_path: str | Path) -> RepositoryInspectResponse:
        """Extract repository metadata and detect a Spring Boot application."""
        repository_path = self._resolve_repository_path(local_path)
        try:
            java_files = tuple(self._java_files(repository_path))
            repository_name = self._repository_name(repository_path)
            has_pom_xml = (repository_path / "pom.xml").is_file()
            has_gradle_build = any(
                (repository_path / filename).is_file()
                for filename in ("build.gradle", "build.gradle.kts")
            )
            main_java_path = repository_path / "src" / "main" / "java"
            has_src_main_java = main_java_path.is_dir()
            application_class = self._find_spring_boot_application(
                java_files,
                main_java_path,
            )
        except OSError as error:
            logger.exception(
                "Repository inspection failed",
                extra={"local_path": repository_path},
            )
            raise RepositoryInspectionError("Unable to inspect repository files.") from error

        is_spring_boot = (
            has_pom_xml and has_src_main_java and application_class is not None
        )
        response = RepositoryInspectResponse(
            repository_name=repository_name,
            primary_language="Java" if java_files else "Unknown",
            build_tool=self._build_tool(has_pom_xml, has_gradle_build),
            java_file_count=len(java_files),
            has_src_main_java=has_src_main_java,
            has_pom_xml=has_pom_xml,
            has_gradle_build=has_gradle_build,
            is_spring_boot=is_spring_boot,
            application_class=application_class,
            detection_reason=self._detection_reason(
                has_pom_xml=has_pom_xml,
                has_src_main_java=has_src_main_java,
                application_class=application_class,
            ),
        )
        logger.info(
            "Repository inspection completed",
            extra={
                "local_path": repository_path,
                "repository_name": response.repository_name,
                "is_spring_boot": response.is_spring_boot,
            },
        )
        return response

    @staticmethod
    def _resolve_repository_path(local_path: str | Path) -> Path:
        """Resolve and validate the supplied repository directory."""
        repository_path = Path(local_path).expanduser().resolve()
        if not repository_path.is_dir():
            raise InvalidRepositoryPathError(
                "Repository path must exist and reference a directory."
            )
        return repository_path

    @staticmethod
    def _java_files(repository_path: Path) -> list[Path]:
        """Return Java files while excluding Git metadata."""
        return [
            path
            for path in repository_path.rglob("*.java")
            if ".git" not in path.relative_to(repository_path).parts
        ]

    @staticmethod
    def _repository_name(repository_path: Path) -> str:
        """Use the origin URL when available, falling back to the directory name."""
        git_config_path = repository_path / ".git" / "config"
        if not git_config_path.is_file():
            return repository_path.name

        config = git_config_path.read_text(encoding="utf-8", errors="ignore")
        origin_url_match = _GIT_ORIGIN_URL_PATTERN.search(config)
        if origin_url_match is None:
            return repository_path.name

        repository_name = origin_url_match.group(1).rstrip("/").rsplit("/", 1)[-1]
        if repository_name.endswith(".git"):
            repository_name = repository_name[:-4]
        return repository_name or repository_path.name

    @staticmethod
    def _build_tool(has_pom_xml: bool, has_gradle_build: bool) -> str:
        """Identify the repository build tool from its standard build files."""
        if has_pom_xml:
            return "Maven"
        if has_gradle_build:
            return "Gradle"
        return "Unknown"

    @staticmethod
    def _find_spring_boot_application(
        java_files: tuple[Path, ...],
        main_java_path: Path,
    ) -> str | None:
        """Find the annotated Spring Boot application class without AST parsing."""
        for java_file in java_files:
            if not java_file.is_relative_to(main_java_path):
                continue
            source = java_file.read_text(encoding="utf-8", errors="ignore")
            annotation_match = _SPRING_BOOT_APPLICATION_PATTERN.search(source)
            if annotation_match is None:
                continue

            class_match = _CLASS_PATTERN.search(source, annotation_match.end())
            if class_match is None:
                continue
            package_match = _PACKAGE_PATTERN.search(source)
            class_name = class_match.group(1)
            if package_match is None:
                return class_name
            return f"{package_match.group(1)}.{class_name}"
        return None

    @staticmethod
    def _detection_reason(
        *,
        has_pom_xml: bool,
        has_src_main_java: bool,
        application_class: str | None,
    ) -> str:
        """Describe the evidence used for Spring Boot detection."""
        if has_pom_xml and has_src_main_java and application_class is not None:
            return (
                "Detected pom.xml, src/main/java, and @SpringBootApplication "
                f"on {application_class}."
            )

        missing_signals: list[str] = []
        if not has_pom_xml:
            missing_signals.append("pom.xml")
        if not has_src_main_java:
            missing_signals.append("src/main/java")
        if application_class is None:
            missing_signals.append("@SpringBootApplication annotation")
        return "Not detected: missing " + ", ".join(missing_signals) + "."
