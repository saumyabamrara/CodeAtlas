"""Service health endpoint."""

from fastapi import APIRouter, status

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Report that the HTTP service is available."""
    return {"status": "healthy", "service": "CodeAtlas Backend"}
