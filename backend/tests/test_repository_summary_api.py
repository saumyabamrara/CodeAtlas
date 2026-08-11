"""API tests for frontend-ready repository summaries."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.dependencies.repositories import get_analysis_service
from app.exceptions.repository import InvalidRepositoryPathError
from app.schemas.repositories import (
    DependencyMetadata,
    JavaClassMetadata,
    JavaFileMetadata,
    RepositoryAnalyzeResponse,
)
from main import create_application


class StubAnalysisService:
    """Return configured analysis metadata while tracking request count."""

    def __init__(self, *, invalid: bool = False) -> None:
        self.calls = 0
        self.invalid = invalid

    def analyze_repository(self, local_path: str) -> RepositoryAnalyzeResponse:
        self.calls += 1
        if self.invalid:
            raise InvalidRepositoryPathError(
                "Repository path must exist and reference a directory."
            )
        source = JavaClassMetadata(
            file_path="Source.java",
            package_name="com.example",
            class_name="Source",
            qualified_class_name="Source",
            annotations=[],
            methods=[],
            scope="production",
        )
        target = JavaClassMetadata(
            file_path="Target.java",
            package_name="com.example",
            class_name="Target",
            qualified_class_name="Target",
            annotations=[],
            methods=[],
            scope="production",
        )
        return RepositoryAnalyzeResponse(
            total_java_files=2,
            parsed_successfully=2,
            parse_failures=0,
            files=[
                JavaFileMetadata(
                    file_path="Source.java",
                    scope="production",
                    parsed_successfully=True,
                ),
                JavaFileMetadata(
                    file_path="Target.java",
                    scope="production",
                    parsed_successfully=True,
                ),
            ],
            classes=[source, target],
            controllers=[],
            services=[],
            repositories=[],
            endpoints=[],
            dependencies=[
                DependencyMetadata(
                    file_path="Source.java",
                    package_name="com.example",
                    source_class_name="Source",
                    source_qualified_class_name="Source",
                    target_type="Target",
                    dependency_kind="field",
                    source_scope="production",
                )
            ],
        )


def test_repository_summary_endpoint_uses_one_analysis_pass() -> None:
    application = create_application()
    analysis_service = StubAnalysisService()
    application.dependency_overrides[get_analysis_service] = lambda: analysis_service

    response = TestClient(application).post(
        "/repositories/summary",
        json={"local_path": "repo"},
    )

    assert response.status_code == 200
    assert analysis_service.calls == 1
    assert response.json() == {
        "total_java_files": 2,
        "parsed_successfully": 2,
        "parse_failures": 0,
        "class_count": 2,
        "controller_count": 0,
        "service_count": 0,
        "repository_count": 0,
        "endpoint_count": 0,
        "dependency_count": 1,
        "graph_node_count": 2,
        "graph_edge_count": 1,
        "production_java_files": 2,
        "test_java_files": 0,
        "production_class_count": 2,
        "test_class_count": 0,
        "production_dependency_count": 1,
        "test_dependency_count": 0,
    }


def test_repository_summary_endpoint_preserves_invalid_path_error() -> None:
    application = create_application()
    analysis_service = StubAnalysisService(invalid=True)
    application.dependency_overrides[get_analysis_service] = lambda: analysis_service

    response = TestClient(application).post(
        "/repositories/summary",
        json={"local_path": "missing"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Repository path must exist and reference a directory."
    }


def test_repository_summary_endpoint_matches_petclinic_counts() -> None:
    repository_path = Path(
        r"E:\Project\CodeAtlas\backend\workspace\spring-petclinic-65c70b2eaf6a4c528db2efbaa4b51b00"
    )
    if not repository_path.is_dir():
        pytest.skip("Expected Spring PetClinic workspace is unavailable.")

    response = TestClient(create_application()).post(
        "/repositories/summary",
        json={"local_path": str(repository_path)},
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_java_files": 49,
        "parsed_successfully": 49,
        "parse_failures": 0,
        "class_count": 49,
        "controller_count": 6,
        "service_count": 0,
        "repository_count": 3,
        "endpoint_count": 17,
        "dependency_count": 67,
        "graph_node_count": 25,
        "graph_edge_count": 7,
        "production_java_files": 30,
        "test_java_files": 19,
        "production_class_count": 25,
        "test_class_count": 24,
        "production_dependency_count": 21,
        "test_dependency_count": 46,
    }
