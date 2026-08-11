"""Tests for explicit declared Java dependency extraction."""

from app.analyzers.dependency_analyzer import DependencyAnalyzer
from app.services.java_parser_service import (
    JavaClassDeclaration,
    JavaCompilationUnit,
    JavaConstructorDeclaration,
    JavaFieldDeclaration,
    JavaParameterDeclaration,
)


def _field(name: str, type_name: str) -> JavaFieldDeclaration:
    return JavaFieldDeclaration(
        name=name,
        type=type_name,
        visibility="private",
        annotations=(),
    )


def _constructor(*parameters: tuple[str, str]) -> JavaConstructorDeclaration:
    return JavaConstructorDeclaration(
        visibility="public",
        annotations=(),
        parameters=tuple(
            JavaParameterDeclaration(name=name, type=type_name, annotations=())
            for name, type_name in parameters
        ),
    )


def _analyze(class_declaration: JavaClassDeclaration):  # type: ignore[no-untyped-def]
    return DependencyAnalyzer().analyze(
        file_path="Example.java",
        compilation_unit=JavaCompilationUnit(
            package_name="com.example",
            classes=(class_declaration,),
        ),
    )


def test_extracts_field_and_constructor_dependencies_with_constructor_precedence() -> None:
    declaration = JavaClassDeclaration(
        class_name="OwnerController",
        qualified_class_name="OwnerController",
        annotations=(),
        fields=(
            _field("ownerService", "OwnerService"),
            _field("alternateOwnerService", "OwnerService"),
            _field("cache", "Map<String, Owner>"),
        ),
        constructors=(
            _constructor(
                ("service", "OwnerService"),
                ("repository", "OwnerRepository"),
                ("backupRepository", "OwnerRepository"),
            ),
        ),
    )

    dependencies = _analyze(declaration)

    assert {
        (dependency.target_type, dependency.dependency_kind)
        for dependency in dependencies
    } == {
        ("OwnerService", "constructor_parameter"),
        ("Map<String, Owner>", "field"),
        ("OwnerRepository", "constructor_parameter"),
    }
    assert all(dependency.file_path == "Example.java" for dependency in dependencies)
    assert all(dependency.package_name == "com.example" for dependency in dependencies)
    assert all(dependency.source_class_name == "OwnerController" for dependency in dependencies)


def test_dependency_identity_uses_declared_type_not_variable_or_class_name() -> None:
    declaration = JavaClassDeclaration(
        class_name="NameOnlyRepository",
        qualified_class_name="Outer.NameOnlyRepository",
        annotations=(),
        fields=(
            _field("OwnerService", "String"),
            _field("repository", "Integer"),
        ),
    )

    dependencies = _analyze(declaration)

    assert [dependency.target_type for dependency in dependencies] == ["String", "Integer"]
    assert all(
        dependency.source_qualified_class_name == "Outer.NameOnlyRepository"
        for dependency in dependencies
    )


def test_class_without_declared_fields_or_constructor_parameters_has_no_dependencies() -> None:
    declaration = JavaClassDeclaration(
        class_name="OwnerService",
        qualified_class_name="OwnerService",
        annotations=(),
        constructors=(_constructor(),),
    )

    assert _analyze(declaration) == []
