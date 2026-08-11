"""Repository HTTP endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.dependencies.repositories import (
    AnalysisServiceDependency,
    ArchitectureGraphServiceDependency,
    PackageAnalysisServiceDependency,
    RepositoryInspectorDependency,
    RepositoryServiceDependency,
    RepositorySummaryServiceDependency,
)
from app.exceptions.repository import (
    InvalidRepositoryPathError,
    InvalidRepositoryUrlError,
    RepositoryAnalysisError,
    RepositoryCloneError,
    RepositoryInspectionError,
)
from app.schemas.repositories import (
    ArchitectureGraph,
    PackageAnalysisResponse,
    RepositoryAnalyzeRequest,
    RepositoryAnalyzeResponse,
    RepositoryControllersResponse,
    RepositoryCloneRequest,
    RepositoryCloneResponse,
    RepositoryInspectRequest,
    RepositoryInspectResponse,
    RepositorySummary,
)

router = APIRouter(prefix="/repositories")


@router.post(
    "/clone",
    response_model=RepositoryCloneResponse,
    status_code=status.HTTP_201_CREATED,
)
def clone_repository(
    payload: RepositoryCloneRequest,
    repository_service: RepositoryServiceDependency,
) -> RepositoryCloneResponse:
    """Clone a public GitHub repository."""
    try:
        return repository_service.clone_repository(payload.repository_url)
    except InvalidRepositoryUrlError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except RepositoryCloneError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Repository cloning failed.",
        ) from error


@router.post("/inspect", response_model=RepositoryInspectResponse)
def inspect_repository(
    payload: RepositoryInspectRequest,
    repository_inspector: RepositoryInspectorDependency,
) -> RepositoryInspectResponse:
    """Inspect metadata for a cloned repository."""
    try:
        return repository_inspector.inspect_repository(payload.local_path)
    except InvalidRepositoryPathError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except RepositoryInspectionError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository inspection failed.",
        ) from error


@router.post("/analyze", response_model=RepositoryAnalyzeResponse)
def analyze_repository(
    payload: RepositoryAnalyzeRequest,
    analysis_service: AnalysisServiceDependency,
) -> RepositoryAnalyzeResponse:
    """Parse all Java source files in a cloned repository."""
    try:
        return analysis_service.analyze_repository(payload.local_path)
    except InvalidRepositoryPathError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except RepositoryAnalysisError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository analysis failed.",
        ) from error


@router.post("/graph", response_model=ArchitectureGraph)
def build_architecture_graph(
    payload: RepositoryAnalyzeRequest,
    analysis_service: AnalysisServiceDependency,
    graph_service: ArchitectureGraphServiceDependency,
) -> ArchitectureGraph:
    """Analyze a repository once and transform the result into a graph."""
    try:
        analysis = analysis_service.analyze_repository(payload.local_path)
        return graph_service.build_graph(analysis)
    except InvalidRepositoryPathError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except RepositoryAnalysisError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository analysis failed.",
        ) from error


@router.post("/summary", response_model=RepositorySummary)
def build_repository_summary(
    payload: RepositoryAnalyzeRequest,
    analysis_service: AnalysisServiceDependency,
    graph_service: ArchitectureGraphServiceDependency,
    summary_service: RepositorySummaryServiceDependency,
) -> RepositorySummary:
    """Analyze once and derive a frontend-ready repository summary."""
    try:
        analysis = analysis_service.analyze_repository(payload.local_path)
        graph = graph_service.build_graph(analysis)
        return summary_service.build_summary(analysis, graph)
    except InvalidRepositoryPathError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except RepositoryAnalysisError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository analysis failed.",
        ) from error


@router.post("/packages", response_model=PackageAnalysisResponse)
def build_package_analysis(
    payload: RepositoryAnalyzeRequest,
    analysis_service: AnalysisServiceDependency,
    package_service: PackageAnalysisServiceDependency,
) -> PackageAnalysisResponse:
    """Analyze once and derive package-level architecture metadata."""
    try:
        analysis = analysis_service.analyze_repository(payload.local_path)
        return package_service.build_package_analysis(analysis)
    except InvalidRepositoryPathError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except RepositoryAnalysisError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository analysis failed.",
        ) from error


@router.post("/controllers", response_model=RepositoryControllersResponse)
def extract_controllers(
    payload: RepositoryAnalyzeRequest,
    analysis_service: AnalysisServiceDependency,
) -> RepositoryControllersResponse:
    """Extract Spring controller classes from a cloned repository."""
    try:
        return analysis_service.extract_controllers(payload.local_path)
    except InvalidRepositoryPathError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except RepositoryAnalysisError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository controller extraction failed.",
        ) from error
