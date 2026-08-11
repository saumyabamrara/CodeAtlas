"""Dependencies for repository-related routes."""

from typing import Annotated

from fastapi import Depends, Request

from app.analyzers.controller_analyzer import ControllerAnalyzer
from app.analyzers.dependency_analyzer import DependencyAnalyzer
from app.analyzers.endpoint_analyzer import EndpointAnalyzer
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.service_analyzer import ServiceAnalyzer
from app.core.config import Settings
from app.services.analysis_service import AnalysisService
from app.services.architecture_graph_service import ArchitectureGraphService
from app.services.java_parser_service import JavaParserService
from app.services.package_analysis_service import PackageAnalysisService
from app.services.repository_service import RepositoryService
from app.services.repository_inspector import RepositoryInspector
from app.services.repository_summary_service import RepositorySummaryService
from app.services.source_scope_service import SourceScopeService


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
        ),
        controller_analyzer=ControllerAnalyzer(),
        service_analyzer=ServiceAnalyzer(),
        repository_analyzer=RepositoryAnalyzer(),
        endpoint_analyzer=EndpointAnalyzer(),
        dependency_analyzer=DependencyAnalyzer(),
        source_scope_service=SourceScopeService(),
    )


AnalysisServiceDependency = Annotated[
    AnalysisService,
    Depends(get_analysis_service),
]


def get_architecture_graph_service() -> ArchitectureGraphService:
    """Provide the repository-analysis graph transformer."""
    return ArchitectureGraphService()


ArchitectureGraphServiceDependency = Annotated[
    ArchitectureGraphService,
    Depends(get_architecture_graph_service),
]


def get_repository_summary_service() -> RepositorySummaryService:
    """Provide the repository summary transformer."""
    return RepositorySummaryService()


RepositorySummaryServiceDependency = Annotated[
    RepositorySummaryService,
    Depends(get_repository_summary_service),
]


def get_package_analysis_service(
    graph_service: ArchitectureGraphServiceDependency,
) -> PackageAnalysisService:
    """Provide package analysis using the canonical graph transformer."""
    return PackageAnalysisService(graph_service)


PackageAnalysisServiceDependency = Annotated[
    PackageAnalysisService,
    Depends(get_package_analysis_service),
]
