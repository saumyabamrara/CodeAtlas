"""Repository cloning operations."""

import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from git import GitCommandError, Repo

from app.exceptions.repository import InvalidRepositoryUrlError, RepositoryCloneError
from app.schemas.repositories import RepositoryCloneResponse

logger = logging.getLogger(__name__)

_GITHUB_COMPONENT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class RepositoryService:
    """Clone public GitHub repositories into the configured workspace."""

    def __init__(self, workspace_directory: Path) -> None:
        self._workspace_directory = workspace_directory.expanduser().resolve()

    def clone_repository(self, repository_url: str) -> RepositoryCloneResponse:
        """Clone a validated public GitHub repository and return its metadata."""
        try:
            repository_name = self._repository_name_from_url(repository_url)
        except InvalidRepositoryUrlError:
            logger.warning(
                "Rejected invalid repository URL",
                extra={"repository_url": repository_url},
            )
            raise
        local_path = self._workspace_directory / self._clone_directory_name(repository_name)

        logger.info(
            "Cloning GitHub repository",
            extra={
                "repository_url": repository_url,
                "repository_name": repository_name,
                "local_path": local_path,
            },
        )
        try:
            self._workspace_directory.mkdir(parents=True, exist_ok=True)
            repository = Repo.clone_from(repository_url, local_path)
            default_branch = repository.active_branch.name
        except (GitCommandError, OSError, TypeError) as error:
            logger.exception(
                "Repository clone failed",
                extra={
                    "repository_url": repository_url,
                    "repository_name": repository_name,
                    "local_path": local_path,
                },
            )
            raise RepositoryCloneError(
                f"Unable to clone repository '{repository_name}'."
            ) from error

        clone_timestamp = datetime.now(UTC)
        logger.info(
            "Repository cloned successfully",
            extra={
                "repository_url": repository_url,
                "repository_name": repository_name,
                "local_path": local_path,
            },
        )
        return RepositoryCloneResponse(
            repository_name=repository_name,
            local_path=str(local_path),
            default_branch=default_branch,
            clone_timestamp=clone_timestamp,
        )

    @staticmethod
    def _repository_name_from_url(repository_url: str) -> str:
        """Validate a public HTTPS GitHub URL and extract its repository name."""
        parsed_url = urlparse(repository_url)
        try:
            port = parsed_url.port
        except ValueError as error:
            raise InvalidRepositoryUrlError(
                "Repository URL must be a public HTTPS GitHub repository URL."
            ) from error
        if (
            parsed_url.scheme != "https"
            or parsed_url.hostname is None
            or parsed_url.hostname.lower() != "github.com"
            or parsed_url.username is not None
            or parsed_url.password is not None
            or port is not None
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise InvalidRepositoryUrlError(
                "Repository URL must be a public HTTPS GitHub repository URL."
            )

        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) != 2:
            raise InvalidRepositoryUrlError(
                "Repository URL must include an owner and repository name."
            )

        owner, repository_name = path_parts
        if repository_name.lower().endswith(".git"):
            repository_name = repository_name[:-4]

        if not all(
            component not in {"", ".", ".."}
            and _GITHUB_COMPONENT_PATTERN.fullmatch(component)
            for component in (owner, repository_name)
        ):
            raise InvalidRepositoryUrlError("Repository URL contains an invalid path.")

        return repository_name

    @staticmethod
    def _clone_directory_name(repository_name: str) -> str:
        """Generate an isolated destination so repeated clones do not collide."""
        return f"{repository_name}-{uuid4().hex}"
