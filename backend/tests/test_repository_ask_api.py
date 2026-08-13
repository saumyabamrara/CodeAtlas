"""API tests for the stateless repository architecture assistant."""

import pytest
from fastapi.testclient import TestClient

from app.dependencies.repositories import (
    get_analysis_service,
    get_architecture_context_service,
    get_openrouter_service,
)
from app.exceptions.ai import (
    AIConfigurationError,
    AIProviderError,
    AIProviderTimeoutError,
)
from app.schemas.repositories import (
    ArchitectureGraph,
    PackageAnalysisResponse,
    RepositoryAnalyzeAllResponse,
    RepositoryAnalyzeResponse,
    RepositorySummary,
)
from main import create_application


def build_unified_context() -> RepositoryAnalyzeAllResponse:
    analysis = RepositoryAnalyzeResponse(
        total_java_files=0,
        parsed_successfully=0,
        parse_failures=0,
        files=[],
        classes=[],
        controllers=[],
        services=[],
        repositories=[],
        endpoints=[],
        dependencies=[],
    )
    summary = RepositorySummary(
        total_java_files=0,
        parsed_successfully=0,
        parse_failures=0,
        class_count=0,
        controller_count=0,
        service_count=0,
        repository_count=0,
        endpoint_count=0,
        dependency_count=0,
        graph_node_count=0,
        graph_edge_count=0,
        production_java_files=0,
        test_java_files=0,
        production_class_count=0,
        test_class_count=0,
        production_dependency_count=0,
        test_dependency_count=0,
    )
    return RepositoryAnalyzeAllResponse(
        analysis=analysis,
        summary=summary,
        packages=PackageAnalysisResponse(packages=[], dependencies=[]),
        graph=ArchitectureGraph(nodes=[], edges=[]),
    )


class StubContextService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, RepositoryAnalyzeAllResponse]] = []

    def build_context(
        self,
        question: str,
        context: RepositoryAnalyzeAllResponse,
    ) -> str:
        self.calls.append((question, context))
        return "selected context"


class StubOpenRouterService:
    model = "test/model"

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def answer_question(self, question: str, context: str) -> str:
        self.calls.append((question, context))
        if self.error:
            raise self.error
        return "Grounded architecture answer."


class ForbiddenAnalysisService:
    def __init__(self) -> None:
        self.calls = 0

    def analyze_repository(self, local_path: str) -> RepositoryAnalyzeResponse:
        self.calls += 1
        raise AssertionError("The ask route must not analyze a repository.")


def configured_client(
    context_service: StubContextService,
    openrouter_service: StubOpenRouterService,
    analysis_service: ForbiddenAnalysisService | None = None,
) -> TestClient:
    application = create_application()
    application.dependency_overrides[get_architecture_context_service] = (
        lambda: context_service
    )
    application.dependency_overrides[get_openrouter_service] = (
        lambda: openrouter_service
    )
    if analysis_service is not None:
        application.dependency_overrides[get_analysis_service] = lambda: analysis_service
    return TestClient(application)


def test_repository_ask_returns_answer_from_submitted_context_without_analysis() -> None:
    context = build_unified_context()
    context_service = StubContextService()
    openrouter_service = StubOpenRouterService()
    analysis_service = ForbiddenAnalysisService()
    client = configured_client(context_service, openrouter_service, analysis_service)

    response = client.post(
        "/repositories/ask",
        json={"question": "Explain the architecture", "context": context.model_dump()},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Grounded architecture answer.",
        "model": "test/model",
    }
    assert analysis_service.calls == 0
    assert context_service.calls == [("Explain the architecture", context)]
    assert openrouter_service.calls == [
        ("Explain the architecture", "selected context")
    ]


@pytest.mark.parametrize("question", ["", "x" * 1001])
def test_repository_ask_validates_question_length(question: str) -> None:
    response = configured_client(
        StubContextService(), StubOpenRouterService()
    ).post(
        "/repositories/ask",
        json={"question": question, "context": build_unified_context().model_dump()},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    [
        (
            AIConfigurationError("missing"),
            503,
            "AI assistant is not configured.",
        ),
        (AIProviderError("failed"), 502, "AI provider request failed."),
        (
            AIProviderTimeoutError("timeout"),
            504,
            "AI provider request timed out.",
        ),
    ],
)
def test_repository_ask_maps_stable_ai_errors(
    error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    response = configured_client(
        StubContextService(), StubOpenRouterService(error)
    ).post(
        "/repositories/ask",
        json={
            "question": "Explain the architecture",
            "context": build_unified_context().model_dump(),
        },
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
