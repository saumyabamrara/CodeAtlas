"""Tests for deterministic AI architecture context selection."""

from app.schemas.repositories import (
    ArchitectureGraph,
    ControllerMetadata,
    DependencyMetadata,
    EndpointMetadata,
    GraphEdge,
    GraphNode,
    JavaClassMetadata,
    JavaFileMetadata,
    JavaMethodMetadata,
    PackageAnalysisResponse,
    PackageDependencyMetadata,
    PackageMetadata,
    RepositoryAnalyzeAllResponse,
    RepositoryAnalyzeResponse,
    RepositoryMetadata,
    RepositorySummary,
)
from app.services.architecture_context_service import ArchitectureContextService


def build_context_fixture() -> RepositoryAnalyzeAllResponse:
    owner_controller = JavaClassMetadata(
        file_path=r"E:\Project\CodeAtlas\OwnerController.java",
        package_name="com.example.owner",
        class_name="OwnerController",
        qualified_class_name="OwnerController",
        annotations=["Controller"],
        methods=[
            JavaMethodMetadata(
                method_name="showOwner",
                visibility="public",
                return_type="String",
                annotations=[],
                parameters=[],
            )
        ],
        scope="production",
    )
    owner_repository = JavaClassMetadata(
        file_path=r"C:\Users\developer\OwnerRepository.java",
        package_name="com.example.owner",
        class_name="OwnerRepository",
        qualified_class_name="OwnerRepository",
        annotations=["Repository"],
        methods=[],
        scope="production",
    )
    unrelated = JavaClassMetadata(
        file_path="/home/developer/Unrelated.java",
        package_name="com.example.other",
        class_name="Unrelated",
        qualified_class_name="Unrelated",
        annotations=[],
        methods=[],
        scope="production",
    )
    controller = ControllerMetadata(
        file_path=owner_controller.file_path,
        package_name=owner_controller.package_name,
        class_name=owner_controller.class_name,
        qualified_class_name=owner_controller.qualified_class_name,
        annotations=["Controller"],
        scope="production",
    )
    repository = RepositoryMetadata(
        file_path=owner_repository.file_path,
        package_name=owner_repository.package_name,
        class_name=owner_repository.class_name,
        qualified_class_name=owner_repository.qualified_class_name,
        annotations=["Repository"],
        extended_types=[],
        scope="production",
    )
    analysis = RepositoryAnalyzeResponse(
        total_java_files=3,
        parsed_successfully=3,
        parse_failures=0,
        files=[
            JavaFileMetadata(
                file_path=metadata.file_path,
                scope=metadata.scope,
                parsed_successfully=True,
            )
            for metadata in (owner_controller, owner_repository, unrelated)
        ],
        classes=[unrelated, owner_repository, owner_controller],
        controllers=[controller],
        services=[],
        repositories=[repository],
        endpoints=[
            EndpointMetadata(
                file_path=owner_controller.file_path,
                package_name=owner_controller.package_name,
                controller_class_name=owner_controller.class_name,
                qualified_controller_class_name=owner_controller.qualified_class_name,
                method_name="showOwner",
                http_method="GET",
                path="/owners/{id}",
                scope="production",
            )
        ],
        dependencies=[
            DependencyMetadata(
                file_path=owner_controller.file_path,
                package_name=owner_controller.package_name,
                source_class_name=owner_controller.class_name,
                source_qualified_class_name=owner_controller.qualified_class_name,
                target_type="OwnerRepository",
                dependency_kind="constructor_parameter",
                source_scope="production",
            )
        ],
    )
    summary = RepositorySummary(
        total_java_files=3,
        parsed_successfully=3,
        parse_failures=0,
        class_count=3,
        controller_count=1,
        service_count=0,
        repository_count=1,
        endpoint_count=1,
        dependency_count=1,
        graph_node_count=3,
        graph_edge_count=1,
        production_java_files=3,
        test_java_files=0,
        production_class_count=3,
        test_class_count=0,
        production_dependency_count=1,
        test_dependency_count=0,
    )
    packages = PackageAnalysisResponse(
        packages=[
            PackageMetadata(
                package_name="com.example.owner",
                production_class_count=2,
                test_class_count=0,
                production_controller_count=1,
                test_controller_count=0,
                production_service_count=0,
                test_service_count=0,
                production_repository_count=1,
                test_repository_count=0,
            ),
            PackageMetadata(
                package_name="com.example.other",
                production_class_count=1,
                test_class_count=0,
                production_controller_count=0,
                test_controller_count=0,
                production_service_count=0,
                test_service_count=0,
                production_repository_count=0,
                test_repository_count=0,
            ),
        ],
        dependencies=[
            PackageDependencyMetadata(
                source_package="com.example.owner",
                target_package="com.example.data",
                dependency_count=1,
            )
        ],
    )
    graph = ArchitectureGraph(
        nodes=[
            GraphNode(
                id="com.example.owner.OwnerController",
                label="OwnerController",
                node_type="controller",
                file_path=owner_controller.file_path,
                package_name=owner_controller.package_name,
                qualified_class_name=owner_controller.qualified_class_name,
            ),
            GraphNode(
                id="com.example.owner.OwnerRepository",
                label="OwnerRepository",
                node_type="repository",
                file_path=owner_repository.file_path,
                package_name=owner_repository.package_name,
                qualified_class_name=owner_repository.qualified_class_name,
            ),
            GraphNode(
                id="com.example.other.Unrelated",
                label="Unrelated",
                node_type="class",
                file_path=unrelated.file_path,
                package_name=unrelated.package_name,
                qualified_class_name=unrelated.qualified_class_name,
            ),
        ],
        edges=[
            GraphEdge(
                source="com.example.owner.OwnerController",
                target="com.example.owner.OwnerRepository",
                edge_type="DEPENDS_ON",
            )
        ],
    )
    return RepositoryAnalyzeAllResponse(
        analysis=analysis,
        summary=summary,
        packages=packages,
        graph=graph,
    )


def test_general_architecture_context_contains_repository_wide_metadata() -> None:
    result = ArchitectureContextService().build_context(
        "Explain the architecture overview.", build_context_fixture()
    )

    assert "PACKAGES" in result
    assert "CONTROLLERS" in result
    assert "REPOSITORIES" in result
    assert "GET /owners/{id}" in result
    assert "OwnerController -> com.example.owner.OwnerRepository" in result


def test_exact_class_context_contains_methods_endpoints_dependencies_and_neighbor() -> None:
    result = ArchitectureContextService().build_context(
        "What does OwnerController do?", build_context_fixture()
    )

    assert "MATCHED CLASS" in result
    assert "public String showOwner()" in result
    assert "GET /owners/{id}" in result
    assert "OwnerRepository (constructor_parameter)" in result
    assert "DIRECTLY CONNECTED CLASSES" in result
    assert "role=repository" in result
    assert "Unrelated" not in result


def test_qualified_class_name_matches_the_same_focused_context() -> None:
    service = ArchitectureContextService()
    context = build_context_fixture()

    simple = service.build_context("Explain OwnerController", context)
    qualified = service.build_context(
        "Explain com.example.owner.OwnerController", context
    )

    assert qualified == simple


def test_package_and_category_questions_select_corresponding_metadata() -> None:
    service = ArchitectureContextService()
    context = build_context_fixture()

    package_result = service.build_context("Explain com.example.owner", context)
    category_result = service.build_context("Which repositories exist?", context)

    assert "MATCHED PACKAGE" in package_result
    assert "OwnerController [production]" in package_result
    assert "REPOSITORIES" in category_result
    assert "OwnerRepository" in category_result
    assert "Unrelated" not in category_result


def test_context_is_deterministic() -> None:
    service = ArchitectureContextService()
    context = build_context_fixture()

    assert service.build_context("Explain the architecture", context) == service.build_context(
        "Explain the architecture", context
    )


def test_missing_entity_produces_explicit_marker() -> None:
    result = ArchitectureContextService().build_context(
        "Explain MissingThing", build_context_fixture()
    )

    assert "No directly matching CodeAtlas entity was found." in result


def test_context_never_contains_local_file_paths() -> None:
    result = ArchitectureContextService().build_context(
        "Explain the architecture", build_context_fixture()
    )

    assert r"E:\Project\CodeAtlas" not in result
    assert r"C:\Users" not in result
    assert "/home/developer" not in result


def test_context_respects_maximum_size() -> None:
    service = ArchitectureContextService()
    service.MAX_CONTEXT_CHARACTERS = 300

    result = service.build_context("Explain the architecture", build_context_fixture())

    assert len(result) <= 300
    assert "context truncated" in result
