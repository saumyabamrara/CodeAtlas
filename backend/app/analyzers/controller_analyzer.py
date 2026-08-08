"""Spring controller extraction from JavaParser AST representations."""

from app.schemas.repositories import ControllerMetadata
from app.services.java_parser_service import JavaCompilationUnit

_CONTROLLER_ANNOTATIONS = {
    "RestController": "RestController",
    "Controller": "Controller",
}


class ControllerAnalyzer:
    """Extract Spring controller classes from a parsed Java compilation unit."""

    def analyze(self, compilation_unit: JavaCompilationUnit) -> list[ControllerMetadata]:
        """Return metadata for classes marked as Spring MVC controllers."""
        controllers: list[ControllerMetadata] = []
        for class_declaration in compilation_unit.classes:
            controller_type = self._controller_type(class_declaration.annotations)
            if controller_type is None:
                continue
            controllers.append(
                ControllerMetadata(
                    class_name=class_declaration.class_name,
                    package_name=compilation_unit.package_name,
                    fully_qualified_name=self._fully_qualified_name(
                        package_name=compilation_unit.package_name,
                        qualified_class_name=class_declaration.qualified_class_name,
                    ),
                    controller_type=controller_type,
                )
            )
        return controllers

    @staticmethod
    def _controller_type(annotations: tuple[str, ...]) -> str | None:
        """Resolve a Spring controller annotation from an AST declaration."""
        for annotation in annotations:
            annotation_name = annotation.rsplit(".", maxsplit=1)[-1]
            if annotation_name in _CONTROLLER_ANNOTATIONS:
                return _CONTROLLER_ANNOTATIONS[annotation_name]
        return None

    @staticmethod
    def _fully_qualified_name(*, package_name: str, qualified_class_name: str) -> str:
        """Build a fully qualified class name from AST package and type names."""
        if package_name:
            return f"{package_name}.{qualified_class_name}"
        return qualified_class_name
