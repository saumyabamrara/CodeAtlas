"""Tests for repository Java parsing analysis orchestration."""

from pathlib import Path

from app.analyzers.controller_analyzer import ControllerAnalyzer
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.service_analyzer import ServiceAnalyzer
from app.exceptions.repository import JavaParsingError
from app.schemas.repositories import (
    ControllerMetadata,
    JavaClassMetadata,
    RepositoryMetadata,
    ServiceMetadata,
)
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


def test_analyze_repository_extracts_class_controller_service_and_repository_metadata(
    tmp_path: Path,
) -> None:
    """Analyze response includes all extraction metadata from one parse pass."""
    repository_path = tmp_path / "repo"
    repository_path.mkdir()

    app_java = repository_path / "App.java"
    app_java.write_text("class App {}", encoding="utf-8")
    web_java = repository_path / "WebController.java"
    web_java.write_text("class WebController {}", encoding="utf-8")
    billing_java = repository_path / "BillingService.java"
    billing_java.write_text("class BillingService {}", encoding="utf-8")
    annotated_repository_java = repository_path / "AnnotatedRepository.java"
    annotated_repository_java.write_text("class AnnotatedRepository {}", encoding="utf-8")
    qualified_annotated_repository_java = repository_path / "QualifiedAnnotatedRepository.java"
    qualified_annotated_repository_java.write_text(
        "class QualifiedAnnotatedRepository {}",
        encoding="utf-8",
    )
    jpa_repository_java = repository_path / "JpaAccountStore.java"
    jpa_repository_java.write_text("class JpaAccountStore {}", encoding="utf-8")
    crud_repository_java = repository_path / "CrudAccountStore.java"
    crud_repository_java.write_text("class CrudAccountStore {}", encoding="utf-8")
    paging_repository_java = repository_path / "PagingAccountStore.java"
    paging_repository_java.write_text("class PagingAccountStore {}", encoding="utf-8")
    repository_interface_java = repository_path / "ContractStore.java"
    repository_interface_java.write_text("interface ContractStore {}", encoding="utf-8")
    qualified_repository_interface_java = repository_path / "QualifiedContractStore.java"
    qualified_repository_interface_java.write_text(
        "interface QualifiedContractStore {}",
        encoding="utf-8",
    )
    outer_repository_java = repository_path / "OuterRepositories.java"
    outer_repository_java.write_text("class OuterRepoContainer {}", encoding="utf-8")
    name_only_repository_java = repository_path / "NameOnlyRepository.java"
    name_only_repository_java.write_text("class NameOnlyRepository {}", encoding="utf-8")
    component_java = repository_path / "GenericComponent.java"
    component_java.write_text("class GenericComponent {}", encoding="utf-8")
    plain_type_java = repository_path / "PlainType.java"
    plain_type_java.write_text("class PlainType {}", encoding="utf-8")

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
                        extended_types=(),
                    ),
                    JavaClassDeclaration(
                        class_name="NestedConfig",
                        qualified_class_name="App.NestedConfig",
                        annotations=("Configuration",),
                        extended_types=(),
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
                        extended_types=(),
                    ),
                    JavaClassDeclaration(
                        class_name="InternalController",
                        qualified_class_name="WebController.InternalController",
                        annotations=("Controller",),
                        extended_types=(),
                    ),
                ),
            ),
        ),
        billing_java.resolve(): JavaParserResult(
            file_path=billing_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.billing",
                classes=(
                    JavaClassDeclaration(
                        class_name="BillingService",
                        qualified_class_name="BillingService",
                        annotations=("Service",),
                        extended_types=(),
                    ),
                    JavaClassDeclaration(
                        class_name="NestedBillingService",
                        qualified_class_name="BillingService.NestedBillingService",
                        annotations=("org.springframework.stereotype.Service",),
                        extended_types=(),
                    ),
                ),
            ),
        ),
        annotated_repository_java.resolve(): JavaParserResult(
            file_path=annotated_repository_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.repo",
                classes=(
                    JavaClassDeclaration(
                        class_name="AnnotatedRepository",
                        qualified_class_name="AnnotatedRepository",
                        annotations=("Repository",),
                        extended_types=(),
                    ),
                ),
            ),
        ),
        qualified_annotated_repository_java.resolve(): JavaParserResult(
            file_path=qualified_annotated_repository_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.repo",
                classes=(
                    JavaClassDeclaration(
                        class_name="QualifiedAnnotatedRepository",
                        qualified_class_name="QualifiedAnnotatedRepository",
                        annotations=("org.springframework.stereotype.Repository",),
                        extended_types=(),
                    ),
                ),
            ),
        ),
        jpa_repository_java.resolve(): JavaParserResult(
            file_path=jpa_repository_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.repo",
                classes=(
                    JavaClassDeclaration(
                        class_name="JpaAccountStore",
                        qualified_class_name="JpaAccountStore",
                        annotations=(),
                        extended_types=("JpaRepository<Account, Long>",),
                    ),
                ),
            ),
        ),
        crud_repository_java.resolve(): JavaParserResult(
            file_path=crud_repository_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.repo",
                classes=(
                    JavaClassDeclaration(
                        class_name="CrudAccountStore",
                        qualified_class_name="CrudAccountStore",
                        annotations=(),
                        extended_types=(
                            "org.springframework.data.repository.CrudRepository<Account, Long>",
                        ),
                    ),
                ),
            ),
        ),
        paging_repository_java.resolve(): JavaParserResult(
            file_path=paging_repository_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.repo",
                classes=(
                    JavaClassDeclaration(
                        class_name="PagingAccountStore",
                        qualified_class_name="PagingAccountStore",
                        annotations=(),
                        extended_types=("PagingAndSortingRepository<Account, Long>",),
                    ),
                ),
            ),
        ),
        repository_interface_java.resolve(): JavaParserResult(
            file_path=repository_interface_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.repo",
                classes=(
                    JavaClassDeclaration(
                        class_name="ContractStore",
                        qualified_class_name="ContractStore",
                        annotations=(),
                        extended_types=("Repository<Account, Long>",),
                    ),
                ),
            ),
        ),
        qualified_repository_interface_java.resolve(): JavaParserResult(
            file_path=qualified_repository_interface_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.repo",
                classes=(
                    JavaClassDeclaration(
                        class_name="QualifiedContractStore",
                        qualified_class_name="QualifiedContractStore",
                        annotations=(),
                        extended_types=(
                            "org.springframework.data.repository.Repository<Account, Long>",
                        ),
                    ),
                ),
            ),
        ),
        outer_repository_java.resolve(): JavaParserResult(
            file_path=outer_repository_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.repo",
                classes=(
                    JavaClassDeclaration(
                        class_name="OuterRepoContainer",
                        qualified_class_name="OuterRepoContainer",
                        annotations=(),
                        extended_types=(),
                    ),
                    JavaClassDeclaration(
                        class_name="NestedRepo",
                        qualified_class_name="OuterRepoContainer.NestedRepo",
                        annotations=("Repository",),
                        extended_types=(),
                    ),
                ),
            ),
        ),
        name_only_repository_java.resolve(): JavaParserResult(
            file_path=name_only_repository_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.repo",
                classes=(
                    JavaClassDeclaration(
                        class_name="NameOnlyRepository",
                        qualified_class_name="NameOnlyRepository",
                        annotations=(),
                        extended_types=(),
                    ),
                ),
            ),
        ),
        component_java.resolve(): JavaParserResult(
            file_path=component_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.misc",
                classes=(
                    JavaClassDeclaration(
                        class_name="GenericComponent",
                        qualified_class_name="GenericComponent",
                        annotations=("Component",),
                        extended_types=(),
                    ),
                ),
            ),
        ),
        plain_type_java.resolve(): JavaParserResult(
            file_path=plain_type_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.misc",
                classes=(
                    JavaClassDeclaration(
                        class_name="PlainType",
                        qualified_class_name="PlainType",
                        annotations=("Transactional",),
                        extended_types=("Serializable",),
                    ),
                ),
            ),
        ),
    }

    analysis_service = AnalysisService(
        java_parser_service=StubJavaParserService(results=parser_results),
        controller_analyzer=ControllerAnalyzer(),
        service_analyzer=ServiceAnalyzer(),
        repository_analyzer=RepositoryAnalyzer(),
    )

    response = analysis_service.analyze_repository(repository_path)

    assert response.total_java_files == 14
    assert response.parsed_successfully == 14
    assert response.parse_failures == 0
    assert len(response.classes) == 18
    assert all(isinstance(metadata, JavaClassMetadata) for metadata in response.classes)

    assert len(response.controllers) == 2
    assert all(isinstance(metadata, ControllerMetadata) for metadata in response.controllers)
    assert {metadata.class_name for metadata in response.controllers} == {
        "WebController",
        "InternalController",
    }

    assert len(response.services) == 2
    assert all(isinstance(metadata, ServiceMetadata) for metadata in response.services)
    assert {
        (
            metadata.class_name,
            metadata.qualified_class_name,
            tuple(metadata.annotations),
        )
        for metadata in response.services
    } == {
        ("BillingService", "BillingService", ("Service",)),
        (
            "NestedBillingService",
            "BillingService.NestedBillingService",
            ("org.springframework.stereotype.Service",),
        ),
    }

    assert len(response.repositories) == 8
    assert all(isinstance(metadata, RepositoryMetadata) for metadata in response.repositories)
    assert {
        (
            metadata.class_name,
            metadata.qualified_class_name,
            tuple(metadata.annotations),
            tuple(metadata.extended_types),
        )
        for metadata in response.repositories
    } == {
        ("AnnotatedRepository", "AnnotatedRepository", ("Repository",), ()),
        (
            "QualifiedAnnotatedRepository",
            "QualifiedAnnotatedRepository",
            ("org.springframework.stereotype.Repository",),
            (),
        ),
        ("JpaAccountStore", "JpaAccountStore", (), ("JpaRepository<Account, Long>",)),
        (
            "CrudAccountStore",
            "CrudAccountStore",
            (),
            ("org.springframework.data.repository.CrudRepository<Account, Long>",),
        ),
        (
            "PagingAccountStore",
            "PagingAccountStore",
            (),
            ("PagingAndSortingRepository<Account, Long>",),
        ),
        ("ContractStore", "ContractStore", (), ("Repository<Account, Long>",)),
        (
            "QualifiedContractStore",
            "QualifiedContractStore",
            (),
            ("org.springframework.data.repository.Repository<Account, Long>",),
        ),
        ("NestedRepo", "OuterRepoContainer.NestedRepo", ("Repository",), ()),
    }
    assert all(
        metadata.class_name != "NameOnlyRepository" for metadata in response.repositories
    )
    assert all(metadata.class_name != "GenericComponent" for metadata in response.repositories)


def test_analyze_repository_skips_failed_files_in_all_metadata_lists(tmp_path: Path) -> None:
    """Analyze response excludes failed files from classes/controllers/services/repositories."""
    repository_path = tmp_path / "repo"
    repository_path.mkdir()

    valid_repository_java = repository_path / "ValidRepository.java"
    valid_repository_java.write_text("class ValidRepository {}", encoding="utf-8")
    valid_controller_java = repository_path / "ValidController.java"
    valid_controller_java.write_text("class ValidController {}", encoding="utf-8")
    valid_service_java = repository_path / "ValidService.java"
    valid_service_java.write_text("class ValidService {}", encoding="utf-8")
    valid_plain_java = repository_path / "ValidPlain.java"
    valid_plain_java.write_text("class ValidPlain {}", encoding="utf-8")
    invalid_repository_java = repository_path / "InvalidRepository.java"
    invalid_repository_java.write_text("class InvalidRepository {", encoding="utf-8")

    parser_results = {
        valid_repository_java.resolve(): JavaParserResult(
            file_path=valid_repository_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example",
                classes=(
                    JavaClassDeclaration(
                        class_name="ValidRepository",
                        qualified_class_name="ValidRepository",
                        annotations=(),
                        extended_types=("JpaRepository<Account, Long>",),
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
                        extended_types=(),
                    ),
                ),
            ),
        ),
        valid_service_java.resolve(): JavaParserResult(
            file_path=valid_service_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example",
                classes=(
                    JavaClassDeclaration(
                        class_name="ValidService",
                        qualified_class_name="ValidService",
                        annotations=("Service",),
                        extended_types=(),
                    ),
                ),
            ),
        ),
        valid_plain_java.resolve(): JavaParserResult(
            file_path=valid_plain_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example",
                classes=(
                    JavaClassDeclaration(
                        class_name="ValidPlain",
                        qualified_class_name="ValidPlain",
                        annotations=("Component",),
                        extended_types=(),
                    ),
                ),
            ),
        ),
    }

    analysis_service = AnalysisService(
        java_parser_service=StubJavaParserService(
            results=parser_results,
            failing_paths={invalid_repository_java.resolve()},
        ),
        controller_analyzer=ControllerAnalyzer(),
        service_analyzer=ServiceAnalyzer(),
        repository_analyzer=RepositoryAnalyzer(),
    )

    response = analysis_service.analyze_repository(repository_path)

    assert response.total_java_files == 5
    assert response.parsed_successfully == 4
    assert response.parse_failures == 1
    assert {metadata.class_name for metadata in response.classes} == {
        "ValidRepository",
        "ValidController",
        "ValidService",
        "ValidPlain",
    }
    assert len(response.controllers) == 1
    assert response.controllers[0].class_name == "ValidController"
    assert len(response.services) == 1
    assert response.services[0].class_name == "ValidService"
    assert len(response.repositories) == 1
    assert response.repositories[0].class_name == "ValidRepository"
    assert all(
        metadata.file_path != str(invalid_repository_java.resolve())
        for metadata in response.repositories
    )
