"""Tests for method-level code navigation transformation."""

from app.schemas.repositories import (
    JavaAnnotationMetadata,
    JavaClassMetadata,
    JavaFileMetadata,
    JavaMethodMetadata,
    JavaParameterMetadata,
    RepositoryAnalyzeResponse,
)
from app.services.method_analysis_service import MethodAnalysisService


def _analysis(classes: list[JavaClassMetadata]) -> RepositoryAnalyzeResponse:
    return RepositoryAnalyzeResponse(
        total_java_files=len(classes),
        parsed_successfully=len(classes),
        parse_failures=0,
        files=[
            JavaFileMetadata(
                file_path=metadata.file_path,
                scope=metadata.scope,
                parsed_successfully=True,
            )
            for metadata in classes
        ],
        classes=classes,
        controllers=[],
        services=[],
        repositories=[],
        endpoints=[],
        dependencies=[],
    )


def test_build_method_analysis_preserves_methods_parameters_annotations_and_scope() -> None:
    production_class = JavaClassMetadata(
        file_path="OwnerController.java",
        package_name="com.example.owner",
        class_name="OwnerController",
        qualified_class_name="Outer.OwnerController",
        annotations=[],
        methods=[
            JavaMethodMetadata(
                method_name="findOwner",
                visibility="public",
                return_type="Owner",
                annotations=[
                    JavaAnnotationMetadata(
                        name="GetMapping",
                        value="/owners/{ownerId}",
                        methods=[],
                    )
                ],
                parameters=[
                    JavaParameterMetadata(
                        name="ownerId",
                        type="Integer",
                        annotations=[
                            JavaAnnotationMetadata(
                                name="PathVariable",
                                value="ownerId",
                                methods=[],
                            )
                        ],
                    ),
                    JavaParameterMetadata(
                        name="includeVisits",
                        type="boolean",
                        annotations=[],
                    ),
                ],
            ),
            JavaMethodMetadata(
                method_name="saveOwner",
                visibility="protected",
                return_type="String",
                annotations=[
                    JavaAnnotationMetadata(
                        name="RequestMapping",
                        value="/owners",
                        methods=["POST", "PUT"],
                    )
                ],
                parameters=[],
            ),
        ],
        scope="production",
    )
    test_class = JavaClassMetadata(
        file_path="OwnerControllerTests.java",
        package_name="com.example.owner",
        class_name="OwnerControllerTests",
        qualified_class_name="OwnerControllerTests",
        annotations=[],
        methods=[
            JavaMethodMetadata(
                method_name="findOwnerTest",
                visibility="package-private",
                return_type="void",
                annotations=[],
                parameters=[],
            )
        ],
        scope="test",
    )
    empty_class = JavaClassMetadata(
        file_path="Empty.java",
        package_name="com.example.empty",
        class_name="Empty",
        qualified_class_name="Empty",
        annotations=[],
        methods=[],
        scope="production",
    )

    result = MethodAnalysisService().build_method_analysis(
        _analysis([production_class, test_class, empty_class])
    )

    assert [method.method_name for method in result.methods] == [
        "findOwner",
        "saveOwner",
        "findOwnerTest",
    ]
    find_owner = result.methods[0]
    assert find_owner.file_path == "OwnerController.java"
    assert find_owner.package_name == "com.example.owner"
    assert find_owner.class_name == "OwnerController"
    assert find_owner.qualified_class_name == "Outer.OwnerController"
    assert find_owner.visibility == "public"
    assert find_owner.return_type == "Owner"
    assert find_owner.scope == "production"
    assert [(parameter.name, parameter.type) for parameter in find_owner.parameters] == [
        ("ownerId", "Integer"),
        ("includeVisits", "boolean"),
    ]
    assert find_owner.parameters[0].annotations[0].model_dump() == {
        "name": "PathVariable",
        "value": "ownerId",
        "methods": [],
    }
    assert find_owner.annotations[0].model_dump() == {
        "name": "GetMapping",
        "value": "/owners/{ownerId}",
        "methods": [],
    }
    assert result.methods[1].annotations[0].model_dump() == {
        "name": "RequestMapping",
        "value": "/owners",
        "methods": ["POST", "PUT"],
    }
    assert result.methods[2].scope == "test"


def test_build_method_analysis_returns_empty_methods_for_empty_analysis() -> None:
    result = MethodAnalysisService().build_method_analysis(_analysis([]))

    assert result.methods == []
