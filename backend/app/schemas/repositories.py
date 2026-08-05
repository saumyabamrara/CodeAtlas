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
