"""Request and response schemas for repository operations."""

from datetime import datetime

from pydantic import BaseModel, Field


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


class RepositoryAnalyzeResponse(BaseModel):
    """Summary of Java source parsing results for a repository."""

    total_java_files: int
    parsed_successfully: int
    parse_failures: int
    classes: list[JavaClassMetadata]
    controllers: list["ControllerMetadata"]
    services: list["ServiceMetadata"]
    repositories: list["RepositoryMetadata"]
    endpoints: list["EndpointMetadata"]


class ControllerMetadata(BaseModel):
    """Metadata for one Spring controller class."""

    file_path: str
    package_name: str
    class_name: str
    qualified_class_name: str
    annotations: list[str]


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


class RepositoryMetadata(BaseModel):
    """Metadata for one Spring repository type."""

    file_path: str
    package_name: str
    class_name: str
    qualified_class_name: str
    annotations: list[str]
    extended_types: list[str]


class EndpointMetadata(BaseModel):
    """Metadata for one extracted controller endpoint mapping."""

    file_path: str
    package_name: str
    controller_class_name: str
    qualified_controller_class_name: str
    method_name: str
    http_method: str | None
    path: str
