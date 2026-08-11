"""Tests for repository Java parsing analysis orchestration."""

from pathlib import Path

from app.analyzers.controller_analyzer import ControllerAnalyzer
from app.analyzers.dependency_analyzer import DependencyAnalyzer
from app.analyzers.endpoint_analyzer import EndpointAnalyzer
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.service_analyzer import ServiceAnalyzer
from app.exceptions.repository import JavaParsingError
from app.schemas.repositories import (
    EndpointMetadata,
    DependencyMetadata,
    JavaAnnotationMetadata,
    ControllerMetadata,
    JavaClassMetadata,
    JavaMethodMetadata,
    JavaParameterMetadata,
    RepositoryMetadata,
    ServiceMetadata,
)
from app.services.analysis_service import AnalysisService
from app.services.java_parser_service import (
    JavaAnnotation,
    JavaClassDeclaration,
    JavaCompilationUnit,
    JavaConstructorDeclaration,
    JavaFieldDeclaration,
    JavaMethodDeclaration,
    JavaParameterDeclaration,
    JavaParserResult,
)
from app.services.source_scope_service import SourceScopeService


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
        self.parsed_paths: list[Path] = []

    def parse_file(self, file_path: str | Path) -> JavaParserResult:
        source_path = Path(file_path).resolve()
        self.parsed_paths.append(source_path)
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
                        methods=(
                            JavaMethodDeclaration(
                                method_name="initCreationForm",
                                visibility="public",
                                return_type="String",
                                annotations=(
                                    JavaAnnotation(
                                        name="GetMapping",
                                        value="/pets/new",
                                        methods=(),
                                    ),
                                ),
                                parameters=(),
                            ),
                            JavaMethodDeclaration(
                                method_name="processCreationForm",
                                visibility="package-private",
                                return_type="String",
                                annotations=(
                                    JavaAnnotation(
                                        name="PostMapping",
                                        value="/pets/new",
                                        methods=(),
                                    ),
                                ),
                                parameters=(
                                    JavaParameterDeclaration(
                                        name="ownerId",
                                        type="Integer",
                                        annotations=(
                                            JavaAnnotation(
                                                name="PathVariable",
                                                value="ownerId",
                                                methods=(),
                                            ),
                                        ),
                                    ),
                                    JavaParameterDeclaration(
                                        name="pet",
                                        type="Pet",
                                        annotations=(),
                                    ),
                                ),
                            ),
                        ),
                        fields=(
                            JavaFieldDeclaration(
                                name="billingService",
                                type="BillingService",
                                visibility="private",
                                annotations=(),
                            ),
                        ),
                        constructors=(
                            JavaConstructorDeclaration(
                                visibility="public",
                                annotations=(),
                                parameters=(
                                    JavaParameterDeclaration(
                                        name="service",
                                        type="BillingService",
                                        annotations=(),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    JavaClassDeclaration(
                        class_name="InternalController",
                        qualified_class_name="WebController.InternalController",
                        annotations=("Controller",),
                        extended_types=(),
                        methods=(
                            JavaMethodDeclaration(
                                method_name="internalHealth",
                                visibility="protected",
                                return_type="void",
                                annotations=(
                                    JavaAnnotation(
                                        name="GetMapping",
                                        value="/internal",
                                        methods=(),
                                    ),
                                ),
                                parameters=(),
                            ),
                        ),
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

    parser_service = StubJavaParserService(results=parser_results)
    analysis_service = AnalysisService(
        java_parser_service=parser_service,
        controller_analyzer=ControllerAnalyzer(),
        service_analyzer=ServiceAnalyzer(),
        repository_analyzer=RepositoryAnalyzer(),
        endpoint_analyzer=EndpointAnalyzer(),
        dependency_analyzer=DependencyAnalyzer(),
        source_scope_service=SourceScopeService(),
    )

    response = analysis_service.analyze_repository(repository_path)

    assert response.total_java_files == 14
    assert response.parsed_successfully == 14
    assert response.parse_failures == 0
    assert len(parser_service.parsed_paths) == response.total_java_files
    assert len(set(parser_service.parsed_paths)) == response.total_java_files
    assert len(response.classes) == 18
    assert all(isinstance(metadata, JavaClassMetadata) for metadata in response.classes)
    web_controller_class = next(
        class_metadata
        for class_metadata in response.classes
        if class_metadata.class_name == "WebController"
    )
    assert len(web_controller_class.methods) == 2
    assert all(
        isinstance(method_metadata, JavaMethodMetadata)
        for method_metadata in web_controller_class.methods
    )
    assert {
        (
            method_metadata.method_name,
            method_metadata.visibility,
            method_metadata.return_type,
        )
        for method_metadata in web_controller_class.methods
    } == {
        ("initCreationForm", "public", "String"),
        ("processCreationForm", "package-private", "String"),
    }
    creation_method = next(
        method_metadata
        for method_metadata in web_controller_class.methods
        if method_metadata.method_name == "processCreationForm"
    )
    assert all(
        isinstance(annotation_metadata, JavaAnnotationMetadata)
        for annotation_metadata in creation_method.annotations
    )
    assert all(
        isinstance(parameter_metadata, JavaParameterMetadata)
        for parameter_metadata in creation_method.parameters
    )
    assert {
        (
            parameter_metadata.name,
            parameter_metadata.type,
            tuple(
                (
                    annotation_metadata.name,
                    annotation_metadata.value,
                    tuple(annotation_metadata.methods),
                )
                for annotation_metadata in parameter_metadata.annotations
            ),
        )
        for parameter_metadata in creation_method.parameters
    } == {
        ("ownerId", "Integer", (("PathVariable", "ownerId", ()),)),
        ("pet", "Pet", ()),
    }

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
    assert len(response.endpoints) == 3
    assert all(isinstance(metadata, EndpointMetadata) for metadata in response.endpoints)
    assert {
        (
            metadata.qualified_controller_class_name,
            metadata.method_name,
            metadata.http_method,
            metadata.path,
        )
        for metadata in response.endpoints
    } == {
        ("WebController", "initCreationForm", "GET", "/pets/new"),
        ("WebController", "processCreationForm", "POST", "/pets/new"),
        ("WebController.InternalController", "internalHealth", "GET", "/internal"),
    }
    assert response.dependencies == [
        DependencyMetadata(
            file_path=str(web_java.resolve()),
            package_name="com.example.web",
            source_class_name="WebController",
            source_qualified_class_name="WebController",
            target_type="BillingService",
            dependency_kind="constructor_parameter",
            source_scope="production",
        )
    ]


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
                        methods=(
                            JavaMethodDeclaration(
                                method_name="health",
                                visibility="public",
                                return_type="String",
                                annotations=(
                                    JavaAnnotation(
                                        name="GetMapping",
                                        value="/health",
                                        methods=(),
                                    ),
                                ),
                                parameters=(),
                            ),
                        ),
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
                        fields=(
                            JavaFieldDeclaration(
                                name="service",
                                type="ValidService",
                                visibility="private",
                                annotations=(),
                            ),
                        ),
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
        endpoint_analyzer=EndpointAnalyzer(),
        dependency_analyzer=DependencyAnalyzer(),
        source_scope_service=SourceScopeService(),
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
    assert len(response.endpoints) == 1
    assert response.endpoints[0].method_name == "health"
    assert response.endpoints[0].path == "/health"
    assert len(response.dependencies) == 1
    assert response.dependencies[0].target_type == "ValidService"
    assert all(
        metadata.file_path != str(invalid_repository_java.resolve())
        for metadata in response.repositories
    )
    assert all(
        metadata.file_path != str(invalid_repository_java.resolve())
        for metadata in response.endpoints
    )
    assert all(
        metadata.file_path != str(invalid_repository_java.resolve())
        for metadata in response.dependencies
    )


def test_analyze_repository_includes_method_metadata_shapes_and_visibility(tmp_path: Path) -> None:
    """Class metadata includes detailed method visibility, types, and parameter metadata."""
    repository_path = tmp_path / "repo"
    repository_path.mkdir()

    methods_java = repository_path / "MethodShowcase.java"
    methods_java.write_text("class MethodShowcase {}", encoding="utf-8")

    parser_results = {
        methods_java.resolve(): JavaParserResult(
            file_path=methods_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.methods",
                classes=(
                    JavaClassDeclaration(
                        class_name="MethodShowcase",
                        qualified_class_name="MethodShowcase",
                        annotations=(),
                        methods=(
                            JavaMethodDeclaration(
                                method_name="publicVoid",
                                visibility="public",
                                return_type="void",
                                annotations=(),
                                parameters=(),
                            ),
                            JavaMethodDeclaration(
                                method_name="protectedOwner",
                                visibility="protected",
                                return_type="Owner",
                                annotations=(),
                                parameters=(),
                            ),
                            JavaMethodDeclaration(
                                method_name="privateOwners",
                                visibility="private",
                                return_type="List<Owner>",
                                annotations=(),
                                parameters=(),
                            ),
                            JavaMethodDeclaration(
                                method_name="packageScoped",
                                visibility="package-private",
                                return_type="String",
                                annotations=(
                                    JavaAnnotation(
                                        name="RequestMapping",
                                        value="/methods",
                                        methods=("GET", "POST"),
                                    ),
                                ),
                                parameters=(
                                    JavaParameterDeclaration(
                                        name="ownerId",
                                        type="Integer",
                                        annotations=(
                                            JavaAnnotation(
                                                name="PathVariable",
                                                value="ownerId",
                                                methods=(),
                                            ),
                                        ),
                                    ),
                                    JavaParameterDeclaration(
                                        name="includeVisits",
                                        type="boolean",
                                        annotations=(),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    JavaClassDeclaration(
                        class_name="NestedType",
                        qualified_class_name="MethodShowcase.NestedType",
                        annotations=(),
                        methods=(
                            JavaMethodDeclaration(
                                method_name="nestedMethod",
                                visibility="public",
                                return_type="String",
                                annotations=(),
                                parameters=(),
                            ),
                        ),
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
        endpoint_analyzer=EndpointAnalyzer(),
        dependency_analyzer=DependencyAnalyzer(),
        source_scope_service=SourceScopeService(),
    )

    response = analysis_service.analyze_repository(repository_path)

    assert response.total_java_files == 1
    assert response.parsed_successfully == 1
    assert response.parse_failures == 0
    assert len(response.classes) == 2
    assert response.controllers == []
    assert response.services == []
    assert response.repositories == []
    assert response.endpoints == []
    assert response.dependencies == []

    showcase = next(
        class_metadata
        for class_metadata in response.classes
        if class_metadata.class_name == "MethodShowcase"
    )
    assert {
        (
            method_metadata.method_name,
            method_metadata.visibility,
            method_metadata.return_type,
            len(method_metadata.parameters),
        )
        for method_metadata in showcase.methods
    } == {
        ("publicVoid", "public", "void", 0),
        ("protectedOwner", "protected", "Owner", 0),
        ("privateOwners", "private", "List<Owner>", 0),
        ("packageScoped", "package-private", "String", 2),
    }

    package_scoped = next(
        method_metadata
        for method_metadata in showcase.methods
        if method_metadata.method_name == "packageScoped"
    )
    assert package_scoped.annotations == [
        JavaAnnotationMetadata(
            name="RequestMapping",
            value="/methods",
            methods=["GET", "POST"],
        )
    ]
    assert package_scoped.parameters == [
        JavaParameterMetadata(
            name="ownerId",
            type="Integer",
            annotations=[
                JavaAnnotationMetadata(
                    name="PathVariable",
                    value="ownerId",
                    methods=[],
                )
            ],
        ),
        JavaParameterMetadata(
            name="includeVisits",
            type="boolean",
            annotations=[],
        ),
    ]

    nested_type = next(
        class_metadata
        for class_metadata in response.classes
        if class_metadata.class_name == "NestedType"
    )
    assert nested_type.qualified_class_name == "MethodShowcase.NestedType"
    assert nested_type.methods[0].method_name == "nestedMethod"


def test_analyze_repository_propagates_file_scope_to_all_metadata(tmp_path: Path) -> None:
    """One path-derived scope is shared by every metadata type from a Java file."""
    repository_path = tmp_path / "repo"
    production_java = repository_path / "src" / "main" / "java" / "WebController.java"
    test_java = repository_path / "src" / "test" / "java" / "TestService.java"
    classless_test_java = repository_path / "src" / "test" / "java" / "package-info.java"
    failed_test_java = repository_path / "src" / "test" / "java" / "BrokenTest.java"
    failed_production_java = repository_path / "src" / "main" / "java" / "Broken.java"
    production_java.parent.mkdir(parents=True)
    test_java.parent.mkdir(parents=True)
    production_java.write_text("class WebController {}", encoding="utf-8")
    test_java.write_text("class TestService {}", encoding="utf-8")
    classless_test_java.write_text("package com.example.test;", encoding="utf-8")
    failed_test_java.write_text("class BrokenTest {", encoding="utf-8")
    failed_production_java.write_text("class Broken {", encoding="utf-8")

    parser_results = {
        production_java.resolve(): JavaParserResult(
            file_path=production_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.web",
                classes=(
                    JavaClassDeclaration(
                        class_name="WebController",
                        qualified_class_name="WebController",
                        annotations=("RestController",),
                        methods=(
                            JavaMethodDeclaration(
                                method_name="index",
                                visibility="public",
                                return_type="String",
                                annotations=(
                                    JavaAnnotation(
                                        name="GetMapping",
                                        value="/",
                                        methods=(),
                                    ),
                                ),
                                parameters=(),
                            ),
                        ),
                        fields=(
                            JavaFieldDeclaration(
                                name="repository",
                                type="OwnerRepository",
                                visibility="private",
                                annotations=(),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        test_java.resolve(): JavaParserResult(
            file_path=test_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.test",
                classes=(
                    JavaClassDeclaration(
                        class_name="TestService",
                        qualified_class_name="TestService",
                        annotations=("Service",),
                        extended_types=("Repository<Entity, Long>",),
                        fields=(
                            JavaFieldDeclaration(
                                name="client",
                                type="ExternalClient",
                                visibility="private",
                                annotations=(),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        classless_test_java.resolve(): JavaParserResult(
            file_path=classless_test_java.resolve(),
            compilation_unit=JavaCompilationUnit(
                package_name="com.example.test",
                classes=(),
            ),
        ),
    }
    parser_service = StubJavaParserService(
        results=parser_results,
        failing_paths={failed_test_java.resolve(), failed_production_java.resolve()},
    )
    analysis_service = AnalysisService(
        java_parser_service=parser_service,
        controller_analyzer=ControllerAnalyzer(),
        service_analyzer=ServiceAnalyzer(),
        repository_analyzer=RepositoryAnalyzer(),
        endpoint_analyzer=EndpointAnalyzer(),
        dependency_analyzer=DependencyAnalyzer(),
        source_scope_service=SourceScopeService(),
    )

    response = analysis_service.analyze_repository(repository_path)

    assert response.total_java_files == 5
    assert response.parsed_successfully == 3
    assert response.parse_failures == 2
    assert len(response.files) == 5
    assert {
        (Path(item.file_path).name, item.scope, item.parsed_successfully)
        for item in response.files
    } == {
        ("WebController.java", "production", True),
        ("TestService.java", "test", True),
        ("package-info.java", "test", True),
        ("BrokenTest.java", "test", False),
        ("Broken.java", "production", False),
    }
    assert {item.class_name: item.scope for item in response.classes} == {
        "WebController": "production",
        "TestService": "test",
    }
    assert response.controllers[0].scope == "production"
    assert response.services[0].scope == "test"
    assert response.repositories[0].scope == "test"
    assert response.endpoints[0].scope == "production"
    assert {
        item.source_class_name: item.source_scope for item in response.dependencies
    } == {
        "WebController": "production",
        "TestService": "test",
    }
