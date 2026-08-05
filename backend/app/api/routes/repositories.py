"""Repository HTTP endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.dependencies.repositories import (
    RepositoryInspectorDependency,
    RepositoryServiceDependency,
)
from app.exceptions.repository import (
    InvalidRepositoryPathError,
    InvalidRepositoryUrlError,
    RepositoryCloneError,
    RepositoryInspectionError,
)
from app.schemas.repositories import (
    RepositoryCloneRequest,
    RepositoryCloneResponse,
    RepositoryInspectRequest,
    RepositoryInspectResponse,
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
