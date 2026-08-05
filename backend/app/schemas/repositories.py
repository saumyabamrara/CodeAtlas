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
