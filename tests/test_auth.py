"""Authentication boundary and development identity tests."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_development_identity_is_reported_only_when_explicitly_enabled() -> None:
    settings = Settings(_env_file=None, app_env="development", dev_auth_enabled=True)
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/auth/session", headers={"X-Dev-User": "local-user"})

    assert response.status_code == 200
    assert response.json() == {
        "authenticated": True,
        "development_identity_enabled": True,
        "oidc_configured": False,
        "user": {"subject": "local-user", "is_development_identity": True},
    }


def test_development_identity_is_not_accepted_in_test_environment() -> None:
    settings = Settings(_env_file=None, app_env="test", dev_auth_enabled=True)
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/auth/session", headers={"X-Dev-User": "local-user"})

    assert response.status_code == 200
    assert response.json()["authenticated"] is False
    assert response.json()["development_identity_enabled"] is False


def test_bearer_token_fails_closed_when_oidc_is_unconfigured() -> None:
    token = "arbitrary-token-that-must-never-be-echoed"
    settings = Settings(_env_file=None, app_env="test", dev_auth_enabled=False)
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/auth/session", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 503
    assert response.json()["code"] == "identity_unconfigured"
    assert token not in response.text


def test_production_rejects_development_authentication() -> None:
    with pytest.raises(ValueError, match="Development authentication cannot be enabled"):
        Settings(
            _env_file=None,
            app_env="production",
            dev_auth_enabled=True,
            database_url="postgresql+asyncpg://cosmos:test-only@localhost:5432/cosmos",
            nasa_api_key="safe-test-key",
            oidc_issuer_url="https://identity.example.test",
            oidc_audience="cosmos-test",
        )
