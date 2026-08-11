"""Request and response schemas for repository operations."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.services.source_scope_service import SourceScope


class RepositoryCloneRequest(BaseModel):
    """Payload used to request cloning a public GitHub repository."""

    repository_url: str = Field(
        description="Public HTTPS GitHub repository URL to clone.",
        examples=["https://github.com/owner/repository"],
    )


class RepositoryCloneResponse(BaseModel):
    """Metadata describing a successfully cloned repository."""

    repository_name: str
    local_path: str
    default_branch: str
    clone_timestamp: datetime


class RepositoryInspectRequest(BaseModel):
    """Payload used to request inspection of a cloned repository."""

    local_path: str = Field(description="Local path of the cloned repository.")


class RepositoryInspectResponse(BaseModel):
    """Metadata extracted from a cloned repository."""

    repository_name: str
    primary_language: str
    build_tool: str
    java_file_count: int
    has_src_main_java: bool
    has_pom_xml: bool
    has_gradle_build: bool
    is_spring_boot: bool
    application_class: str | None
    detection_reason: str


class RepositoryAnalyzeRequest(BaseModel):
    """Payload used to request parsing analysis of a cloned repository."""

    local_path: str = Field(description="Local path of the cloned repository.")


class JavaClassMetadata(BaseModel):
    """Structured metadata for one parsed Java class declaration."""

    file_path: str
    package_name: str
    class_name: str
    qualified_class_name: str
    annotations: list[str]
    methods: list["JavaMethodMetadata"]
    scope: SourceScope


class JavaFileMetadata(BaseModel):
    """File-level parsing result and source scope for one analyzed Java file."""

    file_path: str
    scope: SourceScope
    parsed_successfully: bool


class RepositoryAnalyzeResponse(BaseModel):
    """Summary of Java source parsing results for a repository."""

    total_java_files: int
    parsed_successfully: int
    parse_failures: int
    files: list[JavaFileMetadata]
    classes: list[JavaClassMetadata]
    controllers: list["ControllerMetadata"]
    services: list["ServiceMetadata"]
    repositories: list["RepositoryMetadata"]
    endpoints: list["EndpointMetadata"]
    dependencies: list["DependencyMetadata"]


class ControllerMetadata(BaseModel):
    """Metadata for one Spring controller class."""

    file_path: str
    package_name: str
    class_name: str
    qualified_class_name: str
    annotations: list[str]
    scope: SourceScope


class RepositoryControllersResponse(BaseModel):
    """Controller classes extracted from a cloned repository."""

    controller_count: int
    controllers: list[ControllerMetadata]


class ServiceMetadata(BaseModel):
    """Metadata for one Spring service class."""

    file_path: str
    package_name: str
    class_name: str
    qualified_class_name: str
    annotations: list[str]
    scope: SourceScope


class RepositoryMetadata(BaseModel):
    """Metadata for one Spring repository type."""

    file_path: str
    package_name: str
    class_name: str
    qualified_class_name: str
    annotations: list[str]
    extended_types: list[str]
    scope: SourceScope


class EndpointMetadata(BaseModel):
    """Metadata for one extracted controller endpoint mapping."""

    file_path: str
    package_name: str
    controller_class_name: str
    qualified_controller_class_name: str
    method_name: str
    http_method: str | None
    path: str
    scope: SourceScope


class JavaAnnotationMetadata(BaseModel):
    """Structured metadata for one Java annotation."""

    name: str
    value: str | None
    methods: list[str]


class JavaParameterMetadata(BaseModel):
    """Structured metadata for one Java method parameter."""

    name: str
    type: str
    annotations: list[JavaAnnotationMetadata]


class JavaMethodMetadata(BaseModel):
    """Structured metadata for one Java method declaration."""

    method_name: str
    visibility: str
    return_type: str
    annotations: list[JavaAnnotationMetadata]
    parameters: list[JavaParameterMetadata]


class DependencyMetadata(BaseModel):
    """Metadata for one explicit class-level Java dependency."""

    file_path: str
    package_name: str
    source_class_name: str
    source_qualified_class_name: str
    target_type: str
    dependency_kind: str
    source_scope: SourceScope


class GraphNode(BaseModel):
    """One analyzed Java class represented as an architecture graph node."""

    id: str
    label: str
    node_type: Literal["class", "controller", "service", "repository"]
    file_path: str
    package_name: str
    qualified_class_name: str


class GraphEdge(BaseModel):
    """One relationship between two architecture graph nodes."""

    source: str
    target: str
    edge_type: Literal["DEPENDS_ON"]


class ArchitectureGraph(BaseModel):
    """Canonical graph derived from repository analysis metadata."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class RepositorySummary(BaseModel):
    """Frontend-ready aggregate counts from repository analysis and graph data."""

    total_java_files: int
    parsed_successfully: int
    parse_failures: int
    class_count: int
    controller_count: int
    service_count: int
    repository_count: int
    endpoint_count: int
    dependency_count: int
    graph_node_count: int
    graph_edge_count: int
    production_java_files: int
    test_java_files: int
    production_class_count: int
    test_class_count: int
    production_dependency_count: int
    test_dependency_count: int


class PackageMetadata(BaseModel):
    """Production and test role counts for one analyzed Java package."""

    package_name: str
    production_class_count: int
    test_class_count: int
    production_controller_count: int
    test_controller_count: int
    production_service_count: int
    test_service_count: int
    production_repository_count: int
    test_repository_count: int


class PackageDependencyMetadata(BaseModel):
    """Aggregated production class dependencies between two packages."""

    source_package: str
    target_package: str
    dependency_count: int


class PackageAnalysisResponse(BaseModel):
    """Package-level metadata derived from repository analysis."""

    packages: list[PackageMetadata]
    dependencies: list[PackageDependencyMetadata]
