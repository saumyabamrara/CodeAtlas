"""Tests for the mocked OpenRouter HTTP boundary."""

import json

import httpx
import pytest

from app.exceptions.ai import (
    AIConfigurationError,
    AIProviderError,
    AIProviderTimeoutError,
)
from app.services.openrouter_service import (
    GROUNDING_SYSTEM_PROMPT,
    OPENROUTER_CHAT_COMPLETIONS_URL,
    OpenRouterService,
)


def test_openrouter_request_and_successful_answer_extraction() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "  Grounded answer.  "}}]},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        service = OpenRouterService("secret-key", "configured/model", client=client)
        answer = service.answer_question("What is this?", "Structured metadata")

    assert answer == "Grounded answer."
    assert captured["url"] == OPENROUTER_CHAT_COMPLETIONS_URL
    assert captured["authorization"] == "Bearer secret-key"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["model"] == "configured/model"
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 1_200
    assert payload["reasoning"] == {"effort": "low", "exclude": True}
    assert payload["messages"][0] == {
        "role": "system",
        "content": GROUNDING_SYSTEM_PROMPT,
    }
    assert "--- BEGIN QUESTION ---" in payload["messages"][1]["content"]
    assert "--- BEGIN CODEATLAS DATA ---" in payload["messages"][1]["content"]
    assert "Never invent" in GROUNDING_SYSTEM_PROMPT
    assert "analysis is insufficient" in GROUNDING_SYSTEM_PROMPT


def test_openrouter_rejects_missing_api_key_without_http_request() -> None:
    service = OpenRouterService(None, "configured/model")

    with pytest.raises(AIConfigurationError):
        service.answer_question("Question", "Context")


def test_openrouter_converts_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        service = OpenRouterService("key", "model", client=client)
        with pytest.raises(AIProviderTimeoutError):
            service.answer_question("Question", "Context")


def test_openrouter_converts_network_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        service = OpenRouterService("key", "model", client=client)
        with pytest.raises(AIProviderError):
            service.answer_question("Question", "Context")


def test_openrouter_rejects_non_success_response() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(429, json={"error": {"message": "limited"}})
    )
    with httpx.Client(transport=transport) as client:
        service = OpenRouterService("key", "model", client=client)
        with pytest.raises(AIProviderError):
            service.answer_question("Question", "Context")


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, json={"unexpected": []}),
        httpx.Response(200, json={"error": {"message": "provider failed"}}),
    ],
)
def test_openrouter_rejects_malformed_provider_response(
    response: httpx.Response,
) -> None:
    transport = httpx.MockTransport(lambda request: response)
    with httpx.Client(transport=transport) as client:
        service = OpenRouterService("key", "model", client=client)
        with pytest.raises(AIProviderError):
            service.answer_question("Question", "Context")


@pytest.mark.parametrize("content", ["", "   ", None])
def test_openrouter_rejects_empty_answer(content: object) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
        )
    )
    with httpx.Client(transport=transport) as client:
        service = OpenRouterService("key", "model", client=client)
        with pytest.raises(AIProviderError):
            service.answer_question("Question", "Context")
