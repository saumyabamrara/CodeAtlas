"""Spring endpoint extraction from JavaParser AST representations."""

from app.schemas.repositories import ControllerMetadata, EndpointMetadata
from app.services.java_parser_service import JavaAnnotation, JavaClassDeclaration, JavaCompilationUnit

_CLASS_LEVEL_MAPPING = "RequestMapping"
_METHOD_MAPPINGS = {
    "GetMapping": ("GET",),
    "PostMapping": ("POST",),
    "PutMapping": ("PUT",),
    "DeleteMapping": ("DELETE",),
    "PatchMapping": ("PATCH",),
}
_REQUEST_MAPPING = "RequestMapping"


class EndpointAnalyzer:
    """Extract endpoint metadata from controller classes and mapping annotations."""

    def analyze(
        self,
        *,
        file_path: str,
        compilation_unit: JavaCompilationUnit,
        controllers: list[ControllerMetadata],
    ) -> list[EndpointMetadata]:
        """Return endpoint metadata for methods on known controller classes."""
        controller_names = {controller.qualified_class_name for controller in controllers}
        endpoints: list[EndpointMetadata] = []
        for class_declaration in compilation_unit.classes:
            if class_declaration.qualified_class_name not in controller_names:
                continue
            class_paths = self._class_paths(class_declaration)
            endpoints.extend(
                self._class_endpoints(
                    file_path=file_path,
                    package_name=compilation_unit.package_name,
                    class_declaration=class_declaration,
                    class_paths=class_paths,
                )
            )
        return endpoints

    def _class_endpoints(
        self,
        *,
        file_path: str,
        package_name: str,
        class_declaration: JavaClassDeclaration,
        class_paths: tuple[str, ...],
    ) -> list[EndpointMetadata]:
        endpoints: list[EndpointMetadata] = []
        for method_declaration in class_declaration.methods:
            for annotation in method_declaration.annotations:
                combinations = self._method_mapping_combinations(annotation)
                if not combinations:
                    continue
                for http_method, method_path in combinations:
                    for class_path in class_paths:
                        endpoints.append(
                            EndpointMetadata(
                                file_path=file_path,
                                package_name=package_name,
                                controller_class_name=class_declaration.class_name,
                                qualified_controller_class_name=class_declaration.qualified_class_name,
                                method_name=method_declaration.method_name,
                                http_method=http_method,
                                path=self._join_paths(class_path, method_path),
                            )
                        )
        return endpoints

    @staticmethod
    def _class_paths(class_declaration: JavaClassDeclaration) -> tuple[str, ...]:
        class_paths = tuple(
            EndpointAnalyzer._normalize_path(annotation.value)
            for annotation in class_declaration.annotation_details
            if annotation.name == _CLASS_LEVEL_MAPPING
        )
        return class_paths or ("/",)

    @staticmethod
    def _method_mapping_combinations(
        annotation: JavaAnnotation,
    ) -> list[tuple[str | None, str]]:
        if annotation.name in _METHOD_MAPPINGS:
            return [
                (http_method, EndpointAnalyzer._normalize_path(annotation.value))
                for http_method in _METHOD_MAPPINGS[annotation.name]
            ]
        if annotation.name == _REQUEST_MAPPING:
            http_methods = annotation.methods or (None,)
            return [
                (http_method, EndpointAnalyzer._normalize_path(annotation.value))
                for http_method in http_methods
            ]
        return []

    @staticmethod
    def _normalize_path(path: str | None) -> str:
        if path is None:
            return "/"
        trimmed = path.strip()
        if trimmed == "":
            return "/"
        if not trimmed.startswith("/"):
            trimmed = f"/{trimmed}"
        if len(trimmed) > 1:
            trimmed = trimmed.rstrip("/")
        return trimmed or "/"

    @staticmethod
    def _join_paths(class_path: str, method_path: str) -> str:
        normalized_class_path = EndpointAnalyzer._normalize_path(class_path)
        normalized_method_path = EndpointAnalyzer._normalize_path(method_path)
        if normalized_class_path == "/" and normalized_method_path == "/":
            return "/"
        if normalized_class_path == "/":
            return normalized_method_path
        if normalized_method_path == "/":
            return normalized_class_path
        return (
            normalized_class_path.rstrip("/")
            + "/"
            + normalized_method_path.lstrip("/")
        )
