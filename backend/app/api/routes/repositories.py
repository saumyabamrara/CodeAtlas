"""Repository HTTP endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.dependencies.repositories import RepositoryServiceDependency
from app.exceptions.repository import InvalidRepositoryUrlError, RepositoryCloneError
from app.schemas.repositories import RepositoryCloneRequest, RepositoryCloneResponse

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
