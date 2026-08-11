"""API tests for method-level repository navigation."""

from fastapi.testclient import TestClient

from app.dependencies.repositories import get_analysis_service
from app.schemas.repositories import (
    JavaAnnotationMetadata,
    JavaClassMetadata,
    JavaFileMetadata,
    JavaMethodMetadata,
    RepositoryAnalyzeResponse,
)
from main import create_application


class StubAnalysisService:
    """Return existing method metadata while tracking analysis passes."""

    def __init__(self) -> None:
        self.calls = 0

    def analyze_repository(self, local_path: str) -> RepositoryAnalyzeResponse:
        self.calls += 1
        java_class = JavaClassMetadata(
            file_path="Controller.java",
            package_name="com.example",
            class_name="Controller",
            qualified_class_name="Controller",
            annotations=[],
            methods=[
                JavaMethodMetadata(
                    method_name="index",
                    visibility="public",
                    return_type="String",
                    annotations=[
                        JavaAnnotationMetadata(
                            name="GetMapping",
                            value="/",
                            methods=[],
                        )
                    ],
                    parameters=[],
                )
            ],
            scope="production",
        )
        return RepositoryAnalyzeResponse(
            total_java_files=1,
            parsed_successfully=1,
            parse_failures=0,
            files=[
                JavaFileMetadata(
                    file_path=java_class.file_path,
                    scope=java_class.scope,
                    parsed_successfully=True,
                )
            ],
            classes=[java_class],
            controllers=[],
            services=[],
            repositories=[],
            endpoints=[],
            dependencies=[],
        )


def test_repository_methods_endpoint_uses_one_analysis_pass() -> None:
    application = create_application()
    analysis_service = StubAnalysisService()
    application.dependency_overrides[get_analysis_service] = lambda: analysis_service

    response = TestClient(application).post(
        "/repositories/methods",
        json={"local_path": "repo"},
    )

    assert response.status_code == 200
    assert analysis_service.calls == 1
    assert response.json() == {
        "methods": [
            {
                "file_path": "Controller.java",
                "package_name": "com.example",
                "class_name": "Controller",
                "qualified_class_name": "Controller",
                "method_name": "index",
                "visibility": "public",
                "return_type": "String",
                "parameters": [],
                "annotations": [
                    {
                        "name": "GetMapping",
                        "value": "/",
                        "methods": [],
                    }
                ],
                "scope": "production",
            }
        ]
    }


def test_repository_methods_endpoint_rejects_invalid_request_shape() -> None:
    response = TestClient(create_application()).post("/repositories/methods", json={})

    assert response.status_code == 422
