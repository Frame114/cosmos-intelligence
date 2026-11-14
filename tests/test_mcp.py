"""MCP authorization, catalog and bounded-input tests."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import cast

import httpx
import pytest
import respx
from mcp.server.auth.provider import AccessToken
from mcp.server.mcpserver import Context

import app.mcp.server as mcp_module
from app.core.auth import UserContext
from app.core.config import Settings


class StubVerifier:
    def __init__(self, access_token: AccessToken | None) -> None:
        self.access_token = access_token

    async def verify_token(self, _token: str) -> AccessToken | None:
        return self.access_token


def _context(token: str) -> Context:
    return cast(Context, SimpleNamespace(headers={"Authorization": f"Bearer {token}"}))


@pytest.mark.asyncio
async def test_local_mcp_token_is_development_only() -> None:
    development = Settings(_env_file=None, app_env="development", dev_auth_enabled=True)
    verifier = mcp_module.CosmosTokenVerifier(development, "http://localhost:8080/mcp")

    allowed = await verifier.verify_token("local:test.user")
    malformed = await verifier.verify_token("local:contains spaces")

    production = Settings(
        _env_file=None,
        app_env="production",
        dev_auth_enabled=False,
        database_url="postgresql+asyncpg://user:pass@localhost:5432/cosmos",
        oidc_issuer_url="https://identity.example.test",
        oidc_audience="cosmos-api",
        nasa_api_key="test-key",
    )
    prod_verifier = mcp_module.CosmosTokenVerifier(production, "https://cosmos.example.test/mcp")
    rejected = await prod_verifier.verify_token("local:test.user")

    assert allowed is not None
    assert allowed.subject == "test.user"
    assert set(allowed.scopes) == {mcp_module.READ_SCOPE, mcp_module.REPORT_SCOPE}
    assert malformed is None
    assert rejected is None


@pytest.mark.asyncio
async def test_oidc_mcp_token_uses_validated_subject_scopes_and_roles(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        app_env="development",
        dev_auth_enabled=False,
        oidc_issuer_url="https://identity.example.test",
        oidc_audience="cosmos-api",
    )
    verifier = mcp_module.CosmosTokenVerifier(settings, "http://localhost:8080/mcp")
    monkeypatch.setattr(
        mcp_module,
        "_decode_access_token",
        lambda *_args: UserContext(
            "oidc-user",
            frozenset({"cosmos:read"}),
            frozenset({"cosmos_admin"}),
        ),
    )

    access_token = await verifier.verify_token("signed-test-token")

    assert access_token is not None
    assert access_token.subject == "oidc-user"
    assert access_token.scopes == ["cosmos:read"]
    assert access_token.claims == {
        "is_development_identity": False,
        "roles": ["cosmos_admin"],
    }


@pytest.mark.asyncio
async def test_mcp_routes_forward_only_verified_local_identity(monkeypatch) -> None:
    access_token = AccessToken(
        token="local:workspace-owner",
        client_id="local-test",
        scopes=[mcp_module.READ_SCOPE],
        resource="http://localhost:8080/mcp",
        subject="workspace-owner",
        claims={"is_development_identity": True, "roles": []},
    )
    monkeypatch.setattr(mcp_module, "token_verifier", StubVerifier(access_token))
    with respx.mock(base_url="http://127.0.0.1:8000") as router:
        route = router.get("/api/v1/astronomy/records").mock(
            return_value=httpx.Response(200, json={"items": [], "total": 0})
        )
        result = await mcp_module._api_request(
            _context("local:workspace-owner"),
            "GET",
            "/api/v1/astronomy/records",
            params={"page": 1, "page_size": 20},
        )

    assert route.called
    assert route.calls[0].request.headers["X-Dev-User"] == "workspace-owner"
    assert "Authorization" not in route.calls[0].request.headers
    assert result == {"items": [], "total": 0}


@pytest.mark.asyncio
async def test_mcp_tool_catalog_and_limits_are_explicit() -> None:
    tools = await mcp_module.server.list_tools()
    resources = await mcp_module.server.list_resources()
    prompts = await mcp_module.server.list_prompts()
    tool_names = {item.name for item in tools}

    assert len(tool_names) == 10
    assert {
        "search_astronomy_records",
        "get_astronomy_picture",
        "search_asteroids",
        "get_asteroid_details",
        "compare_asteroids",
        "search_space_weather_events",
        "get_space_weather_summary",
        "search_earth_events",
        "search_nasa_media",
        "generate_scientific_report",
    } == tool_names
    assert len(resources) == 2
    assert len(await mcp_module.server.list_resource_templates()) == 2
    assert len(prompts) == 3
    assert mcp_module._validate_page(1, 51)["error"]["code"] == "invalid_input"
    assert mcp_module._validate_window(date(2026, 1, 1), date(2027, 1, 1), 366) is None
    assert (
        mcp_module._validate_window(date(2026, 1, 1), date(2027, 1, 2), 366)["error"]["code"]
        == "invalid_input"
    )


@pytest.mark.asyncio
async def test_mcp_tools_reject_invalid_inputs_before_calling_rest() -> None:
    context = _context("local:validation-user")
    invalid_search = await mcp_module.search_astronomy_records(context, query=" ")
    invalid_asteroid = await mcp_module.get_asteroid_details(context, "not-numeric")
    invalid_compare = await mcp_module.compare_asteroids(context, ["123", "123"])
    invalid_space_type = await mcp_module.search_space_weather_events(
        context,
        ["unsupported"],
        date(2026, 1, 1),
        date(2026, 1, 2),
    )
    invalid_weather_window = await mcp_module.get_space_weather_summary(
        context,
        date(2026, 1, 1),
        date(2026, 1, 31),
    )
    invalid_earth_bbox = await mcp_module.search_earth_events(context, bbox=[-100, 20])
    invalid_earth_status = await mcp_module.search_earth_events(context, status="unknown")
    invalid_media = await mcp_module.search_nasa_media(context, query=" ")
    invalid_report = await mcp_module.generate_scientific_report(context, question=" ")
    invalid_resource = await mcp_module.read_public_record("UNKNOWN", "1", context)
    invalid_report_id = await mcp_module.read_owned_report("bad-id", context)

    assert invalid_search["error"]["code"] == "invalid_input"
    assert invalid_asteroid["error"]["code"] == "invalid_input"
    assert invalid_compare["error"]["code"] == "invalid_input"
    assert invalid_space_type["error"]["code"] == "invalid_input"
    assert invalid_weather_window["error"]["code"] == "invalid_input"
    assert invalid_earth_bbox["error"]["code"] == "invalid_input"
    assert invalid_earth_status["error"]["code"] == "invalid_input"
    assert invalid_media["error"]["code"] == "invalid_input"
    assert invalid_report["error"]["code"] == "invalid_input"
    assert '"invalid_input"' in invalid_resource
    assert '"invalid_input"' in invalid_report_id
