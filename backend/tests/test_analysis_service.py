"""Tests for repository Java parsing analysis orchestration."""

from pathlib import Path

from app.analyzers.controller_analyzer import ControllerAnalyzer
from app.exceptions.repository import JavaParsingError
from app.schemas.repositories import ControllerMetadata, JavaClassMetadata
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


def test_analyze_repository_extracts_class_and_controller_metadata(tmp_path: Path) -> None:
    """Analyze response includes class metadata and controller extraction results."""
    repository_path = tmp_path / "repo"
    repository_path.mkdir()

    app_java = repository_path / "App.java"
    app_java.write_text("class App {}", encoding="utf-8")
    service_java = repository_path / "UserService.java"
    service_java.write_text("class UserService {}", encoding="utf-8")
    web_java = repository_path / "WebController.java"
    web_java.write_text("class WebController {}", encoding="utf-8")
    admin_java = repository_path / "AdminController.java"
    admin_java.write_text("class AdminController {}", encoding="utf-8")
    root_java = repository_path / "Root.java"
    root_java.write_text("class Root {}", encoding="utf-8")

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
        web_java.resolve(): JavaParserResult(
            file_path=web_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.web",
                classes=(
                    JavaClassDeclaration(
                        class_name="WebController",
                        qualified_class_name="WebController",
                        annotations=("RestController",),
                    ),
                    JavaClassDeclaration(
                        class_name="InternalController",
                        qualified_class_name="WebController.InternalController",
                        annotations=("Controller",),
                    ),
                ),
            ),
        ),
        admin_java.resolve(): JavaParserResult(
            file_path=admin_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.admin",
                classes=(
                    JavaClassDeclaration(
                        class_name="AdminController",
                        qualified_class_name="AdminController",
                        annotations=("org.springframework.stereotype.Controller",),
                    ),
                ),
            ),
        ),
        root_java.resolve(): JavaParserResult(
            file_path=root_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="",
                classes=(
                    JavaClassDeclaration(
                        class_name="RootController",
                        qualified_class_name="RootController",
                        annotations=("Controller",),
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

    assert response.total_java_files == 5
    assert response.parsed_successfully == 5
    assert response.parse_failures == 0
    assert len(response.classes) == 7
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
        (
            str(web_java.resolve()),
            "com.example.web",
            "WebController",
            "WebController",
            ("RestController",),
        ),
        (
            str(web_java.resolve()),
            "com.example.web",
            "InternalController",
            "WebController.InternalController",
            ("Controller",),
        ),
        (
            str(admin_java.resolve()),
            "com.example.admin",
            "AdminController",
            "AdminController",
            ("org.springframework.stereotype.Controller",),
        ),
        (
            str(root_java.resolve()),
            "",
            "RootController",
            "RootController",
            ("Controller",),
        ),
    }
    assert len(response.controllers) == 4
    assert all(isinstance(metadata, ControllerMetadata) for metadata in response.controllers)
    assert {
        (
            metadata.file_path,
            metadata.package_name,
            metadata.class_name,
            metadata.qualified_class_name,
            tuple(metadata.annotations),
        )
        for metadata in response.controllers
    } == {
        (
            str(web_java.resolve()),
            "com.example.web",
            "WebController",
            "WebController",
            ("RestController",),
        ),
        (
            str(web_java.resolve()),
            "com.example.web",
            "InternalController",
            "WebController.InternalController",
            ("Controller",),
        ),
        (
            str(admin_java.resolve()),
            "com.example.admin",
            "AdminController",
            "AdminController",
            ("org.springframework.stereotype.Controller",),
        ),
        (
            str(root_java.resolve()),
            "",
            "RootController",
            "RootController",
            ("Controller",),
        ),
    }


def test_analyze_repository_skips_failed_files_in_class_and_controller_metadata(
    tmp_path: Path,
) -> None:
    """Analyze response excludes metadata for files that fail to parse."""
    repository_path = tmp_path / "repo"
    repository_path.mkdir()

    valid_java = repository_path / "Valid.java"
    valid_java.write_text("class Valid {}", encoding="utf-8")
    valid_controller_java = repository_path / "ValidController.java"
    valid_controller_java.write_text("class ValidController {}", encoding="utf-8")
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
        valid_controller_java.resolve(): JavaParserResult(
            file_path=valid_controller_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example",
                classes=(
                    JavaClassDeclaration(
                        class_name="ValidController",
                        qualified_class_name="ValidController",
                        annotations=("RestController",),
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

    assert response.total_java_files == 3
    assert response.parsed_successfully == 2
    assert response.parse_failures == 1
    assert {
        metadata.class_name for metadata in response.classes
    } == {"Valid", "ValidController"}
    assert all(
        metadata.file_path != str(invalid_java.resolve()) for metadata in response.classes
    )
    assert len(response.controllers) == 1
    assert response.controllers[0].class_name == "ValidController"
    assert response.controllers[0].file_path == str(valid_controller_java.resolve())
