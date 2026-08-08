"""Tests for JavaParserService AST deserialization."""

from app.services.java_parser_service import JavaParserService


def test_compilation_unit_deserializes_extended_types() -> None:
    """Parser payload includes extended/implemented type names per declaration."""
    payload = (
        '{"package_name":"com.example",'
        '"classes":[{"class_name":"UserRepository",'
        '"qualified_class_name":"UserRepository",'
        '"annotations":["Repository"],'
        '"extended_types":["JpaRepository<User, Long>","Serializable"]}]}'
    )

    compilation_unit = JavaParserService._compilation_unit(payload)

    assert compilation_unit.package_name == "com.example"
    assert len(compilation_unit.classes) == 1
    assert compilation_unit.classes[0].class_name == "UserRepository"
    assert compilation_unit.classes[0].qualified_class_name == "UserRepository"
    assert compilation_unit.classes[0].annotations == ("Repository",)
    assert compilation_unit.classes[0].extended_types == (
        "JpaRepository<User, Long>",
        "Serializable",
    )
