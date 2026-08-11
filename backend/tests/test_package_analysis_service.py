"""Tests for package-level architecture transformation."""

from app.schemas.repositories import (
    ControllerMetadata,
    DependencyMetadata,
    JavaClassMetadata,
    JavaFileMetadata,
    RepositoryAnalyzeResponse,
    RepositoryMetadata,
    ServiceMetadata,
)
from app.services.architecture_graph_service import ArchitectureGraphService
from app.services.package_analysis_service import PackageAnalysisService


def _class(name: str, package: str, scope: str = "production") -> JavaClassMetadata:
    return JavaClassMetadata(
        file_path=f"{name}.java",
        package_name=package,
        class_name=name,
        qualified_class_name=name,
        annotations=[],
        methods=[],
        scope=scope,
    )


def _dependency(
    source: JavaClassMetadata,
    target_type: str,
    kind: str = "field",
) -> DependencyMetadata:
    return DependencyMetadata(
        file_path=source.file_path,
        package_name=source.package_name,
        source_class_name=source.class_name,
        source_qualified_class_name=source.qualified_class_name,
        target_type=target_type,
        dependency_kind=kind,
        source_scope=source.scope,
    )


def test_build_package_analysis_groups_scoped_roles_and_dependencies() -> None:
    package_a = "com.example.a"
    package_b = "com.example.b"
    package_c = "com.example.testonly"
    a1 = _class("A1", package_a)
    a2 = _class("A2", package_a)
    a3 = _class("A3", package_a)
    a_test = _class("ATest", package_a, "test")
    target = _class("Target", package_b)
    b_test = _class("BTest", package_b, "test")
    only_test = _class("OnlyTest", package_c, "test")
    shared_one = _class("Shared", "com.example.one")
    shared_two = _class("Shared", "com.example.two")
    classes = [
        a1,
        a2,
        a3,
        a_test,
        target,
        b_test,
        only_test,
        shared_one,
        shared_two,
    ]
    analysis = RepositoryAnalyzeResponse(
        total_java_files=len(classes),
        parsed_successfully=len(classes),
        parse_failures=0,
        files=[
            JavaFileMetadata(
                file_path=metadata.file_path,
                scope=metadata.scope,
                parsed_successfully=True,
            )
            for metadata in classes
        ],
        classes=classes,
        controllers=[
            ControllerMetadata(
                **a1.model_dump(exclude={"methods"}),
            ),
            ControllerMetadata(
                **a_test.model_dump(exclude={"methods"}),
            ),
        ],
        services=[
            ServiceMetadata(**a2.model_dump(exclude={"methods"})),
            ServiceMetadata(**only_test.model_dump(exclude={"methods"})),
        ],
        repositories=[
            RepositoryMetadata(
                **target.model_dump(exclude={"methods"}),
                extended_types=[],
            ),
            RepositoryMetadata(
                **b_test.model_dump(exclude={"methods"}),
                extended_types=[],
            ),
        ],
        endpoints=[],
        dependencies=[
            _dependency(a1, "Target"),
            _dependency(a1, "Target", "constructor_parameter"),
            _dependency(a2, "Target"),
            _dependency(a3, "Target"),
            _dependency(a1, "A2"),
            _dependency(a_test, "Target"),
            _dependency(a1, "ExternalClient"),
            _dependency(a1, "Shared"),
        ],
    )

    result = PackageAnalysisService(
        ArchitectureGraphService()
    ).build_package_analysis(analysis)

    packages = {metadata.package_name: metadata for metadata in result.packages}
    assert set(packages) == {
        package_a,
        package_b,
        package_c,
        "com.example.one",
        "com.example.two",
    }
    assert packages[package_a].model_dump() == {
        "package_name": package_a,
        "production_class_count": 3,
        "test_class_count": 1,
        "production_controller_count": 1,
        "test_controller_count": 1,
        "production_service_count": 1,
        "test_service_count": 0,
        "production_repository_count": 0,
        "test_repository_count": 0,
    }
    assert packages[package_b].production_repository_count == 1
    assert packages[package_b].test_repository_count == 1
    assert packages[package_c].production_class_count == 0
    assert packages[package_c].test_class_count == 1
    assert packages[package_c].test_service_count == 1
    assert [metadata.model_dump() for metadata in result.dependencies] == [
        {
            "source_package": package_a,
            "target_package": package_b,
            "dependency_count": 3,
        }
    ]


def test_build_package_analysis_returns_empty_result_for_empty_analysis() -> None:
    analysis = RepositoryAnalyzeResponse(
        total_java_files=0,
        parsed_successfully=0,
        parse_failures=0,
        files=[],
        classes=[],
        controllers=[],
        services=[],
        repositories=[],
        endpoints=[],
        dependencies=[],
    )

    result = PackageAnalysisService(
        ArchitectureGraphService()
    ).build_package_analysis(analysis)

    assert result.packages == []
    assert result.dependencies == []
