"""Tests for JavaParserService AST deserialization."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.config import Settings
from app.exceptions.repository import JavaParsingError
from app.services.java_parser_service import JavaParserService


def test_compilation_unit_deserializes_extended_types_and_method_annotations() -> None:
    """Parser payload includes method visibility, return type, and parameter metadata."""
    payload = (
        '{"package_name":"com.example",'
        '"classes":[{"class_name":"UserRepository",'
        '"qualified_class_name":"UserRepository",'
        '"annotations":["Repository"],'
        '"extended_types":["JpaRepository<User, Long>","Serializable"],'
        '"annotation_details":[{"name":"Repository","value":null,"methods":[]}],'
        '"methods":[{"method_name":"listUsers","visibility":"public","return_type":"List<User>",'
        '"annotations":[{"name":"GetMapping","value":"/users","methods":[]}],'
        '"parameters":[{"name":"ownerId","type":"Integer","annotations":[{"name":"PathVariable","value":"ownerId","methods":[]}]}]}]}]}'
    )

    compilation_unit = JavaParserService._compilation_unit(payload)

    assert compilation_unit.package_name == "com.example"
    assert len(compilation_unit.classes) == 1
    class_declaration = compilation_unit.classes[0]
    assert class_declaration.class_name == "UserRepository"
    assert class_declaration.qualified_class_name == "UserRepository"
    assert class_declaration.annotations == ("Repository",)
    assert class_declaration.extended_types == (
        "JpaRepository<User, Long>",
        "Serializable",
    )
    assert len(class_declaration.annotation_details) == 1
    assert class_declaration.annotation_details[0].name == "Repository"
    assert class_declaration.annotation_details[0].value is None
    assert class_declaration.annotation_details[0].methods == ()
    assert len(class_declaration.methods) == 1
    method_declaration = class_declaration.methods[0]
    assert method_declaration.method_name == "listUsers"
    assert method_declaration.visibility == "public"
    assert method_declaration.return_type == "List<User>"
    assert method_declaration.annotations[0].name == "GetMapping"
    assert method_declaration.annotations[0].value == "/users"
    assert len(method_declaration.parameters) == 1
    assert method_declaration.parameters[0].name == "ownerId"
    assert method_declaration.parameters[0].type == "Integer"
    assert method_declaration.parameters[0].annotations[0].name == "PathVariable"
    assert method_declaration.parameters[0].annotations[0].value == "ownerId"


def test_parse_file_raises_when_bridge_output_lacks_feature10_fields(tmp_path: Path) -> None:
    """Parsing fails loudly when bridge output is missing method-level Feature 10 fields."""
    java_file = tmp_path / "Any.java"
    java_file.write_text("class Any {}", encoding="utf-8")

    class StubParserService(JavaParserService):
        def __init__(self) -> None:
            self._runner_jar = java_file
            self._java_executable = "java"

    parser_service = StubParserService()
    parser_service._java_executable = "java"

    def run(*args, **kwargs):  # type: ignore[no-untyped-def]
        class Result:
            returncode = 0
            stdout = (
                '{"package_name":"com.example","classes":[{"class_name":"Any",'
                '"qualified_class_name":"Any","annotations":[],"extended_types":[],'
                '"annotation_details":[],"methods":[{"method_name":"any","annotations":[],"parameters":[]}]}]}'
            )
            stderr = ""

        return Result()

    with patch("subprocess.run", side_effect=run):
        with pytest.raises(JavaParsingError):
            parser_service.parse_file(java_file)


def test_parse_file_reads_petclinic_controller_methods_and_mappings() -> None:
    """PetClinic PetController parsing includes methods and Spring mapping annotations."""
    workspace_path = Path(r"E:\Project\CodeAtlas\backend\workspace")
    pet_controller_matches = sorted(
        workspace_path.glob(
            "spring-petclinic-*/src/main/java/org/springframework/samples/petclinic/owner/PetController.java"
        )
    )
    if not pet_controller_matches:
        pytest.skip("PetClinic controller file not available in workspace clone.")
    pet_controller_path = pet_controller_matches[-1]

    settings = Settings()
    parser_service = JavaParserService(settings.java_parser_runner_jar, settings.java_executable)
    result = parser_service.parse_file(pet_controller_path)
    classes = result.compilation_unit.classes
    assert classes
    controller_class = next(
        class_declaration
        for class_declaration in classes
        if class_declaration.class_name == "PetController"
    )
    assert controller_class.methods
    assert all(
        method.visibility in {"public", "protected", "private", "package-private"}
        for method in controller_class.methods
    )
    assert all(method.return_type for method in controller_class.methods)
    assert any(
        annotation.name in {"GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping", "RequestMapping"}
        for method in controller_class.methods
        for annotation in method.annotations
    )
    assert any(
        annotation.value is not None and annotation.value.startswith("/")
        for method in controller_class.methods
        for annotation in method.annotations
        if annotation.name in {"GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping", "RequestMapping"}
    )
