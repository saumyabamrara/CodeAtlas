"""Spring controller extraction from JavaParser AST representations."""

from app.schemas.repositories import ControllerMetadata
from app.services.java_parser_service import JavaCompilationUnit

_CONTROLLER_ANNOTATIONS = {
    "RestController": "RestController",
    "Controller": "Controller",
}


class ControllerAnalyzer:
    """Extract Spring controller classes from a parsed Java compilation unit."""

    def analyze(
        self,
        *,
        file_path: str,
        compilation_unit: JavaCompilationUnit,
    ) -> list[ControllerMetadata]:
        """Return metadata for classes marked as Spring MVC controllers."""
        controllers: list[ControllerMetadata] = []
        for class_declaration in compilation_unit.classes:
            if not self._is_controller(class_declaration.annotations):
                continue
            controllers.append(
                ControllerMetadata(
                    file_path=file_path,
                    class_name=class_declaration.class_name,
                    package_name=compilation_unit.package_name,
                    qualified_class_name=class_declaration.qualified_class_name,
                    annotations=list(class_declaration.annotations),
                )
            )
        return controllers

    @staticmethod
    def _is_controller(annotations: tuple[str, ...]) -> bool:
        """Return whether a declaration has a Spring controller annotation."""
        for annotation in annotations:
            annotation_name = annotation.rsplit(".", maxsplit=1)[-1]
            if annotation_name in _CONTROLLER_ANNOTATIONS:
                return True
        return False
