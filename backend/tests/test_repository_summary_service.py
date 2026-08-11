"""Tests for frontend-ready repository summaries."""

from app.schemas.repositories import (
    ArchitectureGraph,
    ControllerMetadata,
    DependencyMetadata,
    EndpointMetadata,
    GraphEdge,
    GraphNode,
    JavaClassMetadata,
    JavaFileMetadata,
    RepositoryAnalyzeResponse,
    RepositoryMetadata,
    ServiceMetadata,
)
from app.services.repository_summary_service import RepositorySummaryService


def test_build_summary_uses_analysis_and_graph_counts_directly() -> None:
    java_class = JavaClassMetadata(
        file_path="Type.java",
        package_name="com.example",
        class_name="Type",
        qualified_class_name="Type",
        annotations=[],
        methods=[],
        scope="production",
    )
    controller = ControllerMetadata(
        file_path="Controller.java",
        package_name="com.example",
        class_name="Controller",
        qualified_class_name="Controller",
        annotations=[],
        scope="production",
    )
    service = ServiceMetadata(
        file_path="Service.java",
        package_name="com.example",
        class_name="Service",
        qualified_class_name="Service",
        annotations=[],
        scope="production",
    )
    repository = RepositoryMetadata(
        file_path="Repository.java",
        package_name="com.example",
        class_name="Repository",
        qualified_class_name="Repository",
        annotations=[],
        extended_types=[],
        scope="production",
    )
    endpoint = EndpointMetadata(
        file_path="Controller.java",
        package_name="com.example",
        controller_class_name="Controller",
        qualified_controller_class_name="Controller",
        method_name="list",
        http_method="GET",
        path="/items",
        scope="production",
    )
    dependency = DependencyMetadata(
        file_path="Controller.java",
        package_name="com.example",
        source_class_name="Controller",
        source_qualified_class_name="Controller",
        target_type="Service",
        dependency_kind="constructor_parameter",
        source_scope="production",
    )
    analysis = RepositoryAnalyzeResponse(
        total_java_files=3,
        parsed_successfully=3,
        parse_failures=0,
        files=[
            JavaFileMetadata(
                file_path="Type.java",
                scope="production",
                parsed_successfully=True,
            ),
            JavaFileMetadata(
                file_path="TypeTests.java",
                scope="test",
                parsed_successfully=True,
            ),
            JavaFileMetadata(
                file_path="package-info.java",
                scope="test",
                parsed_successfully=True,
            ),
        ],
        classes=[
            java_class,
            java_class.model_copy(),
            java_class.model_copy(update={"file_path": "TypeTests.java", "scope": "test"}),
        ],
        controllers=[controller],
        services=[service, service.model_copy()],
        repositories=[repository],
        endpoints=[endpoint, endpoint.model_copy(), endpoint.model_copy()],
        dependencies=[
            dependency,
            dependency.model_copy(update={"source_scope": "test"}),
        ],
    )
    node = GraphNode(
        id="com.example.Type",
        label="Type",
        node_type="class",
        file_path="Type.java",
        package_name="com.example",
        qualified_class_name="Type",
    )
    edge = GraphEdge(
        source="com.example.Type",
        target="com.example.Other",
        edge_type="DEPENDS_ON",
    )
    graph = ArchitectureGraph(
        nodes=[node, node.model_copy(), node.model_copy(), node.model_copy()],
        edges=[edge, edge.model_copy(), edge.model_copy()],
    )

    summary = RepositorySummaryService().build_summary(analysis, graph)

    assert summary.model_dump() == {
        "total_java_files": 3,
        "parsed_successfully": 3,
        "parse_failures": 0,
        "class_count": 3,
        "controller_count": 1,
        "service_count": 2,
        "repository_count": 1,
        "endpoint_count": 3,
        "dependency_count": 2,
        "graph_node_count": 4,
        "graph_edge_count": 3,
        "production_java_files": 1,
        "test_java_files": 2,
        "production_class_count": 2,
        "test_class_count": 1,
        "production_dependency_count": 1,
        "test_dependency_count": 1,
    }
