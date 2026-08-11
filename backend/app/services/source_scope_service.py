"""Classify Java files by conventional production or test source roots."""

from pathlib import Path, PurePosixPath
from typing import Literal

SourceScope = Literal["production", "test"]

_MAIN_SOURCE_ROOT = ("src", "main", "java")
_TEST_SOURCE_ROOT = ("src", "test", "java")


class SourceScopeService:
    """Determine source scope from normalized file path components."""

    def get_scope(self, file_path: str | Path) -> SourceScope:
        """Return test only for files under a conventional test source root."""
        normalized_parts = tuple(
            part.casefold()
            for part in PurePosixPath(str(file_path).replace("\\", "/")).parts
        )
        if self._contains_root(normalized_parts, _MAIN_SOURCE_ROOT):
            return "production"
        if self._contains_root(normalized_parts, _TEST_SOURCE_ROOT):
            return "test"
        return "production"

    @staticmethod
    def _contains_root(parts: tuple[str, ...], root: tuple[str, ...]) -> bool:
        root_size = len(root)
        return any(
            parts[index : index + root_size] == root
            for index in range(len(parts) - root_size + 1)
        )
