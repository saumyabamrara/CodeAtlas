"""API tests for repository architecture graphs."""

from fastapi.testclient import TestClient

from app.dependencies.repositories import get_analysis_service
from app.schemas.repositories import (
    DependencyMetadata,
    JavaClassMetadata,
    RepositoryAnalyzeResponse,
)
from main import create_application


class StubAnalysisService:
    """Return one completed analysis result and track analysis passes."""

    def __init__(self) -> None:
        self.calls = 0

    def analyze_repository(self, local_path: str) -> RepositoryAnalyzeResponse:
        self.calls += 1
        source = JavaClassMetadata(
            file_path="Source.java",
            package_name="com.example",
            class_name="Source",
            qualified_class_name="Source",
            annotations=[],
            methods=[],
        )
        target = JavaClassMetadata(
            file_path="Target.java",
            package_name="com.example",
            class_name="Target",
            qualified_class_name="Target",
            annotations=[],
            methods=[],
        )
        return RepositoryAnalyzeResponse(
            total_java_files=2,
            parsed_successfully=2,
            parse_failures=0,
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
                )
            ],
        )


def test_repository_graph_endpoint_returns_graph_from_one_analysis_pass() -> None:
    application = create_application()
    analysis_service = StubAnalysisService()
    application.dependency_overrides[get_analysis_service] = lambda: analysis_service
    client = TestClient(application)

    response = client.post("/repositories/graph", json={"local_path": "repo"})

    assert response.status_code == 200
    assert analysis_service.calls == 1
    assert response.json() == {
        "nodes": [
            {
                "id": "com.example.Source",
                "label": "Source",
                "node_type": "class",
                "file_path": "Source.java",
                "package_name": "com.example",
                "qualified_class_name": "Source",
            },
            {
                "id": "com.example.Target",
                "label": "Target",
                "node_type": "class",
                "file_path": "Target.java",
                "package_name": "com.example",
                "qualified_class_name": "Target",
            },
        ],
        "edges": [
            {
                "source": "com.example.Source",
                "target": "com.example.Target",
                "edge_type": "DEPENDS_ON",
            }
        ],
    }
