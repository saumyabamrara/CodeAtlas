"""Spring service extraction from JavaParser AST representations."""

from app.schemas.repositories import ServiceMetadata
from app.services.java_parser_service import JavaCompilationUnit
from app.services.source_scope_service import SourceScope

_SERVICE_ANNOTATIONS = {
    "Service",
}


class ServiceAnalyzer:
    """Extract Spring service classes from a parsed Java compilation unit."""

    def analyze(
        self,
        *,
        file_path: str,
        compilation_unit: JavaCompilationUnit,
        scope: SourceScope,
    ) -> list[ServiceMetadata]:
        """Return metadata for classes marked as Spring services."""
        services: list[ServiceMetadata] = []
        for class_declaration in compilation_unit.classes:
            if not self._is_service(class_declaration.annotations):
                continue
            services.append(
                ServiceMetadata(
                    file_path=file_path,
                    package_name=compilation_unit.package_name,
                    class_name=class_declaration.class_name,
                    qualified_class_name=class_declaration.qualified_class_name,
                    annotations=list(class_declaration.annotations),
                    scope=scope,
                )
            )
        return services

    @staticmethod
    def _is_service(annotations: tuple[str, ...]) -> bool:
        """Return whether a declaration has a Spring service annotation."""
        for annotation in annotations:
            annotation_name = annotation.rsplit(".", maxsplit=1)[-1]
            if annotation_name in _SERVICE_ANNOTATIONS:
                return True
        return False
