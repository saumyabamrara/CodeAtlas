"""Spring repository extraction from JavaParser AST representations."""

from app.schemas.repositories import RepositoryMetadata
from app.services.java_parser_service import JavaCompilationUnit
from app.services.source_scope_service import SourceScope

_REPOSITORY_ANNOTATION = "Repository"
_REPOSITORY_PARENT_TYPES = {
    "Repository",
    "CrudRepository",
    "PagingAndSortingRepository",
    "JpaRepository",
}


class RepositoryAnalyzer:
    """Extract Spring repository types from a parsed Java compilation unit."""

    def analyze(
        self,
        *,
        file_path: str,
        compilation_unit: JavaCompilationUnit,
        scope: SourceScope,
    ) -> list[RepositoryMetadata]:
        """Return metadata for classes/interfaces classified as repositories."""
        repositories: list[RepositoryMetadata] = []
        for class_declaration in compilation_unit.classes:
            if not self._is_repository(class_declaration.annotations, class_declaration.extended_types):
                continue
            repositories.append(
                RepositoryMetadata(
                    file_path=file_path,
                    package_name=compilation_unit.package_name,
                    class_name=class_declaration.class_name,
                    qualified_class_name=class_declaration.qualified_class_name,
                    annotations=list(class_declaration.annotations),
                    extended_types=list(class_declaration.extended_types),
                    scope=scope,
                )
            )
        return repositories

    @staticmethod
    def _is_repository(annotations: tuple[str, ...], extended_types: tuple[str, ...]) -> bool:
        """Return whether a declaration has repository annotations or parent types."""
        for annotation in annotations:
            if annotation.rsplit(".", maxsplit=1)[-1] == _REPOSITORY_ANNOTATION:
                return True

        for extended_type in extended_types:
            if RepositoryAnalyzer._simple_type_name(extended_type) in _REPOSITORY_PARENT_TYPES:
                return True

        return False

    @staticmethod
    def _simple_type_name(type_name: str) -> str:
        """Return simple name from possibly qualified/generic Java type name."""
        without_generics = type_name.split("<", maxsplit=1)[0]
        return without_generics.rsplit(".", maxsplit=1)[-1].strip()
