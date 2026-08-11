"""API tests for unified repository dashboard analysis."""

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
    """Return configured analysis metadata while tracking analysis passes."""

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
            package_name="com.source",
            class_name="Source",
            qualified_class_name="Source",
            annotations=[],
            methods=[],
            scope="production",
        )
        target = JavaClassMetadata(
            file_path="Target.java",
            package_name="com.target",
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
                    file_path=metadata.file_path,
                    scope=metadata.scope,
                    parsed_successfully=True,
                )
                for metadata in (source, target)
            ],
            classes=[source, target],
            controllers=[],
            services=[],
            repositories=[],
            endpoints=[],
            dependencies=[
                DependencyMetadata(
                    file_path=source.file_path,
                    package_name=source.package_name,
                    source_class_name=source.class_name,
                    source_qualified_class_name=source.qualified_class_name,
                    target_type="Target",
                    dependency_kind="field",
                    source_scope="production",
                )
            ],
        )


def test_analyze_all_uses_one_analysis_pass_and_returns_all_views() -> None:
    application = create_application()
    analysis_service = StubAnalysisService()
    application.dependency_overrides[get_analysis_service] = lambda: analysis_service

    response = TestClient(application).post(
        "/repositories/analyze-all",
        json={"local_path": "repo"},
    )

    assert response.status_code == 200
    assert analysis_service.calls == 1
    payload = response.json()
    assert set(payload) == {"analysis", "summary", "packages", "graph"}
    assert payload["analysis"]["total_java_files"] == 2
    assert payload["analysis"]["dependencies"][0]["target_type"] == "Target"
    assert payload["summary"]["class_count"] == 2
    assert payload["summary"]["graph_edge_count"] == 1
    assert [item["package_name"] for item in payload["packages"]["packages"]] == [
        "com.source",
        "com.target",
    ]
    assert payload["packages"]["dependencies"] == [
        {
            "source_package": "com.source",
            "target_package": "com.target",
            "dependency_count": 1,
        }
    ]
    assert payload["graph"]["edges"] == [
        {
            "source": "com.source.Source",
            "target": "com.target.Target",
            "edge_type": "DEPENDS_ON",
        }
    ]


def test_analyze_all_preserves_invalid_path_error() -> None:
    application = create_application()
    analysis_service = StubAnalysisService(invalid=True)
    application.dependency_overrides[get_analysis_service] = lambda: analysis_service

    response = TestClient(application).post(
        "/repositories/analyze-all",
        json={"local_path": "missing"},
    )

    assert response.status_code == 404
    assert analysis_service.calls == 1
    assert response.json() == {
        "detail": "Repository path must exist and reference a directory."
    }
