"""Tests for health reporting."""

from fastapi.testclient import TestClient

from main import create_application


def test_health_check() -> None:
    """The service exposes its expected health payload."""
    client = TestClient(create_application())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "CodeAtlas Backend",
    }
