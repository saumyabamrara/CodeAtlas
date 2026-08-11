"""Explicit Java class dependency extraction from parsed declarations."""

from app.schemas.repositories import DependencyMetadata
from app.services.java_parser_service import JavaClassDeclaration, JavaCompilationUnit

_FIELD_DEPENDENCY = "field"
_CONSTRUCTOR_DEPENDENCY = "constructor_parameter"


class DependencyAnalyzer:
    """Extract explicit field and constructor-parameter dependencies."""

    def analyze(
        self,
        *,
        file_path: str,
        compilation_unit: JavaCompilationUnit,
    ) -> list[DependencyMetadata]:
        """Return one dependency per source class + target type with constructor precedence."""
        dependencies: list[DependencyMetadata] = []
        for class_declaration in compilation_unit.classes:
            dependencies.extend(
                self._class_dependencies(
                    file_path=file_path,
                    package_name=compilation_unit.package_name,
                    class_declaration=class_declaration,
                )
            )
        return dependencies

    @staticmethod
    def _class_dependencies(
        *,
        file_path: str,
        package_name: str,
        class_declaration: JavaClassDeclaration,
    ) -> list[DependencyMetadata]:
        dependency_kinds: dict[str, str] = {}

        for field_declaration in class_declaration.fields:
            target_type = field_declaration.type.strip()
            if target_type == "":
                continue
            dependency_kinds.setdefault(target_type, _FIELD_DEPENDENCY)

        for constructor_declaration in class_declaration.constructors:
            for parameter in constructor_declaration.parameters:
                target_type = parameter.type.strip()
                if target_type == "":
                    continue
                dependency_kinds[target_type] = _CONSTRUCTOR_DEPENDENCY

        return [
            DependencyMetadata(
                file_path=file_path,
                package_name=package_name,
                source_class_name=class_declaration.class_name,
                source_qualified_class_name=class_declaration.qualified_class_name,
                target_type=target_type,
                dependency_kind=dependency_kind,
            )
            for target_type, dependency_kind in dependency_kinds.items()
        ]
