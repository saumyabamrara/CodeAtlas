"""Dependencies for repository-related routes."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.services.analysis_service import AnalysisService
from app.services.java_parser_service import JavaParserService
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


def get_analysis_service(request: Request) -> AnalysisService:
    """Provide the repository Java parsing orchestrator."""
    settings: Settings = request.app.state.settings
    return AnalysisService(
        JavaParserService(
            runner_jar=settings.java_parser_runner_jar,
            java_executable=settings.java_executable,
        )
    )


AnalysisServiceDependency = Annotated[
    AnalysisService,
    Depends(get_analysis_service),
]
