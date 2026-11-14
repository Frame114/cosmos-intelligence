"""Smoke tests for FastAPI health and safe error behavior."""

from fastapi import Query
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def _test_settings() -> Settings:
    return Settings(_env_file=None, app_env="test", database_url="")


def test_health_endpoint_returns_ok() -> None:
    with TestClient(create_app(_test_settings())) as client:
        response = client.get("/health/live", headers={"X-Request-ID": "health-test-1"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "cosmos-intelligence",
    }
    assert response.headers["X-Request-ID"] == "health-test-1"


def test_legacy_health_path_remains_available() -> None:
    with TestClient(create_app(_test_settings())) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_fails_closed_when_database_is_not_configured() -> None:
    with TestClient(create_app(_test_settings())) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "database_unconfigured"


def test_openapi_schema_is_available() -> None:
    with TestClient(create_app(_test_settings())) as client:
        response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Cosmos Intelligence API"
    routes = response.json()["paths"]
    assert "/health/live" in routes
    assert "/health/ready" in routes
    assert "/api/v1/asteroids/compare" in routes
    assert "/api/v1/media/{nasa_id}" in routes


def test_production_disables_interactive_api_documentation() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        dev_auth_enabled=False,
        database_url="postgresql+asyncpg://cosmos:test-only@localhost:5432/cosmos",
        nasa_api_key="test-only-nasa-key",
        oidc_issuer_url="https://identity.example.test",
        oidc_audience="cosmos-test",
    )

    with TestClient(create_app(settings)) as client:
        responses = [
            client.get(path)
            for path in ("/docs", "/redoc", "/openapi.json", "/api/v1/openapi.json")
        ]

    assert all(response.status_code == 404 for response in responses)


def test_validation_problem_does_not_echo_user_input() -> None:
    application = create_app(_test_settings())

    @application.get("/_validation-test")
    async def validation_test(value: int = Query(...)) -> dict[str, int]:
        return {"value": value}

    with TestClient(application) as client:
        response = client.get("/_validation-test", params={"value": "secret-like-input"})

    assert response.status_code == 422
    assert "secret-like-input" not in response.text
    assert response.json()["code"] == "validation_error"
