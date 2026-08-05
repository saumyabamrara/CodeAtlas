"""Dependencies for repository-related routes."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.services.repository_service import RepositoryService
from app.services.repository_inspector import RepositoryInspector


def get_repository_service(request: Request) -> RepositoryService:
    """Provide a service configured with the current application's workspace."""
    settings: Settings = request.app.state.settings
    return RepositoryService(settings.repository_workspace)


RepositoryServiceDependency = Annotated[
    RepositoryService,
    Depends(get_repository_service),
]


def get_repository_inspector() -> RepositoryInspector:
    """Provide the repository filesystem inspector."""
    return RepositoryInspector()


RepositoryInspectorDependency = Annotated[
    RepositoryInspector,
    Depends(get_repository_inspector),
]
