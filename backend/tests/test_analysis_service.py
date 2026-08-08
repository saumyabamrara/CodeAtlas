"""Tests for repository Java parsing analysis orchestration."""

from pathlib import Path

from app.analyzers.controller_analyzer import ControllerAnalyzer
from app.exceptions.repository import JavaParsingError
from app.schemas.repositories import JavaClassMetadata
from app.services.analysis_service import AnalysisService
from app.services.java_parser_service import (
    JavaClassDeclaration,
    JavaCompilationUnit,
    JavaParserResult,
)


class StubJavaParserService:
    """Configurable parser double for analysis service tests."""

    def __init__(
        self,
        *,
        results: dict[Path, JavaParserResult],
        failing_paths: set[Path] | None = None,
    ) -> None:
        self._results = results
        self._failing_paths = failing_paths or set()

    def parse_file(self, file_path: str | Path) -> JavaParserResult:
        source_path = Path(file_path).resolve()
        if source_path in self._failing_paths:
            raise JavaParsingError(f"Failed to parse {source_path.name}.")
        return self._results[source_path]


def test_analyze_repository_extracts_class_metadata(tmp_path: Path) -> None:
    """Analyze response includes structured metadata for every parsed class."""
    repository_path = tmp_path / "repo"
    repository_path.mkdir()

    app_java = repository_path / "App.java"
    app_java.write_text("class App {}", encoding="utf-8")
    service_java = repository_path / "UserService.java"
    service_java.write_text("class UserService {}", encoding="utf-8")

    parser_results = {
        app_java.resolve(): JavaParserResult(
            file_path=app_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.app",
                classes=(
                    JavaClassDeclaration(
                        class_name="App",
                        qualified_class_name="App",
                        annotations=("SpringBootApplication",),
                    ),
                    JavaClassDeclaration(
                        class_name="NestedConfig",
                        qualified_class_name="App.NestedConfig",
                        annotations=("Configuration",),
                    ),
                ),
            ),
        ),
        service_java.resolve(): JavaParserResult(
            file_path=service_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.service",
                classes=(
                    JavaClassDeclaration(
                        class_name="UserService",
                        qualified_class_name="UserService",
                        annotations=(),
                    ),
                ),
            ),
        ),
    }

    analysis_service = AnalysisService(
        java_parser_service=StubJavaParserService(results=parser_results),
        controller_analyzer=ControllerAnalyzer(),
    )

    response = analysis_service.analyze_repository(repository_path)

    assert response.total_java_files == 2
    assert response.parsed_successfully == 2
    assert response.parse_failures == 0
    assert len(response.classes) == 3
    assert all(isinstance(metadata, JavaClassMetadata) for metadata in response.classes)
    assert {
        (
            metadata.file_path,
            metadata.package_name,
            metadata.class_name,
            metadata.qualified_class_name,
            tuple(metadata.annotations),
        )
        for metadata in response.classes
    } == {
        (
            str(app_java.resolve()),
            "com.example.app",
            "App",
            "App",
            ("SpringBootApplication",),
        ),
        (
            str(app_java.resolve()),
            "com.example.app",
            "NestedConfig",
            "App.NestedConfig",
            ("Configuration",),
        ),
        (
            str(service_java.resolve()),
            "com.example.service",
            "UserService",
            "UserService",
            (),
        ),
    }


def test_analyze_repository_skips_failed_files_in_class_metadata(tmp_path: Path) -> None:
    """Analyze response excludes class metadata for files that fail to parse."""
    repository_path = tmp_path / "repo"
    repository_path.mkdir()

    valid_java = repository_path / "Valid.java"
    valid_java.write_text("class Valid {}", encoding="utf-8")
    invalid_java = repository_path / "Invalid.java"
    invalid_java.write_text("class Invalid {", encoding="utf-8")

    parser_results = {
        valid_java.resolve(): JavaParserResult(
            file_path=valid_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example",
                classes=(
                    JavaClassDeclaration(
                        class_name="Valid",
                        qualified_class_name="Valid",
                        annotations=("Entity",),
                    ),
                ),
            ),
        ),
    }

    analysis_service = AnalysisService(
        java_parser_service=StubJavaParserService(
            results=parser_results,
            failing_paths={invalid_java.resolve()},
        ),
        controller_analyzer=ControllerAnalyzer(),
    )

    response = analysis_service.analyze_repository(repository_path)

    assert response.total_java_files == 2
    assert response.parsed_successfully == 1
    assert response.parse_failures == 1
    assert len(response.classes) == 1
    assert response.classes[0].file_path == str(valid_java.resolve())
    assert response.classes[0].package_name == "com.example"
    assert response.classes[0].class_name == "Valid"
    assert response.classes[0].qualified_class_name == "Valid"
    assert response.classes[0].annotations == ["Entity"]
