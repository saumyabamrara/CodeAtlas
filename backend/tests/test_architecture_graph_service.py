"""Tests for architecture graph transformation."""

from app.schemas.repositories import (
    ControllerMetadata,
    DependencyMetadata,
    JavaClassMetadata,
    RepositoryAnalyzeResponse,
    RepositoryMetadata,
    ServiceMetadata,
)
from app.services.architecture_graph_service import ArchitectureGraphService


def _class(
    class_name: str,
    *,
    package_name: str = "com.example",
    qualified_class_name: str | None = None,
) -> JavaClassMetadata:
    return JavaClassMetadata(
        file_path=f"{class_name}.java",
        package_name=package_name,
        class_name=class_name,
        qualified_class_name=qualified_class_name or class_name,
        annotations=[],
        methods=[],
    )


def _dependency(
    source: JavaClassMetadata,
    target_type: str,
    dependency_kind: str = "field",
) -> DependencyMetadata:
    return DependencyMetadata(
        file_path=source.file_path,
        package_name=source.package_name,
        source_class_name=source.class_name,
        source_qualified_class_name=source.qualified_class_name,
        target_type=target_type,
        dependency_kind=dependency_kind,
    )


def _analysis(
    *,
    classes: list[JavaClassMetadata],
    controllers: list[ControllerMetadata] | None = None,
    services: list[ServiceMetadata] | None = None,
    repositories: list[RepositoryMetadata] | None = None,
    dependencies: list[DependencyMetadata] | None = None,
) -> RepositoryAnalyzeResponse:
    return RepositoryAnalyzeResponse(
        total_java_files=len(classes),
        parsed_successfully=len(classes),
        parse_failures=0,
        classes=classes,
        controllers=controllers or [],
        services=services or [],
        repositories=repositories or [],
        endpoints=[],
        dependencies=dependencies or [],
    )


def test_build_graph_creates_class_and_nested_nodes_with_stable_ids() -> None:
    ordinary = _class("Ordinary")
    nested = _class("Inner", qualified_class_name="Outer.Inner")

    graph = ArchitectureGraphService().build_graph(
        _analysis(classes=[ordinary, nested])
    )

    assert [(node.id, node.label, node.node_type) for node in graph.nodes] == [
        ("com.example.Ordinary", "Ordinary", "class"),
        ("com.example.Outer.Inner", "Inner", "class"),
    ]


def test_build_graph_uses_existing_roles_with_deterministic_priority() -> None:
    controller_class = _class("WebComponent")
    service_class = _class("BillingComponent")
    repository_class = _class("AccountStore")
    controller_role = ControllerMetadata(
        **controller_class.model_dump(exclude={"methods"})
    )
    service_role = ServiceMetadata(**service_class.model_dump(exclude={"methods"}))
    repository_role = RepositoryMetadata(
        **repository_class.model_dump(exclude={"methods"}),
        extended_types=[],
    )

    graph = ArchitectureGraphService().build_graph(
        _analysis(
            classes=[controller_class, service_class, repository_class],
            controllers=[controller_role],
            services=[
                ServiceMetadata(**controller_class.model_dump(exclude={"methods"})),
                service_role,
            ],
            repositories=[
                RepositoryMetadata(
                    **controller_class.model_dump(exclude={"methods"}),
                    extended_types=[],
                ),
                repository_role,
            ],
        )
    )

    assert len(graph.nodes) == 3
    assert {node.label: node.node_type for node in graph.nodes} == {
        "WebComponent": "controller",
        "BillingComponent": "service",
        "AccountStore": "repository",
    }


def test_build_graph_emits_one_node_per_class_id() -> None:
    duplicated_class = _class("OnlyOnce")

    graph = ArchitectureGraphService().build_graph(
        _analysis(classes=[duplicated_class, duplicated_class.model_copy(deep=True)])
    )

    assert len(graph.nodes) == 1
    assert graph.nodes[0].id == "com.example.OnlyOnce"


def test_build_graph_resolves_dependencies_and_collapses_duplicate_edges() -> None:
    source = _class("Source")
    first_target = _class("FirstTarget", package_name="com.targets")
    second_target = _class("SecondTarget", package_name="com.targets")
    analysis = _analysis(
        classes=[source, first_target, second_target],
        dependencies=[
            _dependency(source, "FirstTarget", "field"),
            _dependency(source, "FirstTarget", "constructor_parameter"),
            _dependency(source, "SecondTarget<String>", "field"),
            _dependency(source, "ExternalClient", "field"),
        ],
    )
    original_analysis = analysis.model_dump()

    graph = ArchitectureGraphService().build_graph(analysis)

    assert {(edge.source, edge.target, edge.edge_type) for edge in graph.edges} == {
        ("com.example.Source", "com.targets.FirstTarget", "DEPENDS_ON"),
        ("com.example.Source", "com.targets.SecondTarget", "DEPENDS_ON"),
    }
    assert len(graph.nodes) == 3
    assert analysis.model_dump() == original_analysis


def test_build_graph_skips_ambiguous_targets_and_nonmatching_sources() -> None:
    source = _class("Source", package_name="com.source")
    first_duplicate = _class("Shared", package_name="com.one")
    second_duplicate = _class("Shared", package_name="com.two")
    wrong_source_package = _class("Source", package_name="com.wrong")

    graph = ArchitectureGraphService().build_graph(
        _analysis(
            classes=[source, first_duplicate, second_duplicate],
            dependencies=[
                _dependency(source, "Shared"),
                _dependency(wrong_source_package, "Shared"),
            ],
        )
    )

    assert graph.edges == []


def test_build_graph_source_resolution_uses_package_and_qualified_class_name() -> None:
    nested_source = _class(
        "Inner",
        package_name="com.source",
        qualified_class_name="Outer.Inner",
    )
    target = _class("Target", package_name="com.target")

    graph = ArchitectureGraphService().build_graph(
        _analysis(
            classes=[nested_source, target],
            dependencies=[_dependency(nested_source, "Target")],
        )
    )

    assert len(graph.edges) == 1
    assert graph.edges[0].source == "com.source.Outer.Inner"
    assert graph.edges[0].target == "com.target.Target"
