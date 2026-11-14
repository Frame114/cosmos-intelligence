"""Private, authenticated MCP server that delegates to the versioned REST API."""

from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from datetime import date
from typing import Any, Literal
from urllib.parse import urlsplit

import httpx
from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import Context
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from app.core.auth import _decode_access_token
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.rate_limit import limiter

MAX_PAGE_SIZE = 50
MAX_TOOL_RESPONSE_BYTES = 512_000
MAX_SPACE_WEATHER_TYPES = 3
READ_SCOPE = "cosmos:read"
REPORT_SCOPE = "research:generate"
DONKI_TYPES = (
    "CME",
    "CMEAnalysis",
    "GST",
    "IPS",
    "FLR",
    "SEP",
    "MPC",
    "RBE",
    "HSS",
    "WSAEnlilSimulations",
    "notifications",
)

_settings = get_settings()
_resource_url = _settings.public_base_url.rstrip("/") + "/mcp"
_api_base_url = os.getenv("COSMOS_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
QueryParam = str | int | float | bool | None


class CosmosTokenVerifier(TokenVerifier):
    """Validate OIDC access tokens, or accept a local-only development token."""

    def __init__(self, settings: Settings, resource_url: str) -> None:
        self.settings = settings
        self.resource_url = resource_url

    async def verify_token(self, token: str) -> AccessToken | None:
        if self.settings.app_env == "development" and self.settings.dev_auth_enabled:
            if token.startswith("local:"):
                subject = token.removeprefix("local:")
                if re.fullmatch(r"[A-Za-z0-9._@-]{1,128}", subject):
                    return AccessToken(
                        token=token,
                        client_id="cosmos-local-development",
                        scopes=[READ_SCOPE, REPORT_SCOPE],
                        resource=self.resource_url,
                        subject=subject,
                        claims={"is_development_identity": True, "roles": []},
                    )
                return None

        if not self.settings.oidc_issuer_url or not self.settings.oidc_audience:
            return None
        try:
            user = await asyncio.to_thread(
                _decode_access_token,
                token,
                self.settings.oidc_issuer_url,
                self.settings.oidc_audience,
            )
        except Exception:
            return None
        return AccessToken(
            token=token,
            client_id="cosmos-oidc",
            scopes=sorted(user.scopes),
            resource=self.resource_url,
            subject=user.subject,
            claims={
                "is_development_identity": False,
                "roles": sorted(user.roles),
            },
        )


token_verifier = CosmosTokenVerifier(_settings, _resource_url)
issuer_url = _settings.oidc_issuer_url or _settings.public_base_url
server = MCPServer(
    name="Cosmos Intelligence",
    version="0.1.0",
    description="Authenticated, bounded access to Cosmos Intelligence public science records.",
    instructions=(
        "Use validated NASA-backed records with explicit units and provenance. "
        "Do not infer impact risk or treat curated records as exhaustive."
    ),
    token_verifier=token_verifier,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(issuer_url),
        resource_server_url=AnyHttpUrl(_resource_url),
        required_scopes=[],
        # OIDC tokens use the configured application audience; the verifier checks it.
        validate_token_resource=False,
    ),
)


def _error(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


def _validate_page(page: int, page_size: int) -> dict[str, Any] | None:
    if page < 1 or page_size < 1 or page_size > MAX_PAGE_SIZE:
        return _error(
            "invalid_input", "Page must be positive and page_size must be between 1 and 50."
        )
    if page > 1000:
        return _error("invalid_input", "Page is above the supported limit.")
    return None


def _validate_window(
    start: date | None, end: date | None, maximum_days: int
) -> dict[str, Any] | None:
    if start is None or end is None:
        return None
    if start > end:
        return _error("invalid_input", "The start date must be on or before the end date.")
    if (end - start).days + 1 > maximum_days:
        return _error("invalid_input", f"The date window must not exceed {maximum_days} days.")
    return None


def _request_bearer(ctx: Context) -> str | None:
    headers: Mapping[str, str] | None = ctx.headers
    if not headers:
        return None
    authorization = next(
        (value for name, value in headers.items() if name.casefold() == "authorization"),
        "",
    )
    if not authorization.startswith("Bearer "):
        return None
    return authorization[7:].strip() or None


async def _api_request(
    ctx: Context,
    method: Literal["GET", "POST"],
    path: str,
    *,
    params: Mapping[str, QueryParam] | None = None,
    body: dict[str, Any] | None = None,
    required_scope: str = READ_SCOPE,
) -> dict[str, Any]:
    raw_token = _request_bearer(ctx)
    if raw_token is None:
        return _error("authentication_required", "A valid access token is required.")
    verified = await token_verifier.verify_token(raw_token)
    if verified is None or verified.subject is None:
        return _error("authentication_required", "A valid access token is required.")
    scopes = set(verified.scopes)
    roles = set((verified.claims or {}).get("roles", []))
    if required_scope not in scopes and "cosmos_admin" not in roles:
        return _error("forbidden", "The required permission is missing.")
    try:
        await limiter.check(
            f"mcp:{verified.subject}",
            _settings.public_rate_limit_per_minute,
        )
    except AppError:
        return _error("rate_limited", "The request limit has been reached.")

    headers: dict[str, str] = {}
    if (verified.claims or {}).get("is_development_identity") is True:
        headers["X-Dev-User"] = verified.subject
    else:
        headers["Authorization"] = f"Bearer {raw_token}"

    try:
        async with httpx.AsyncClient(
            base_url=_api_base_url,
            timeout=httpx.Timeout(25.0, connect=3.0),
            follow_redirects=False,
        ) as client:
            response = await client.request(
                method,
                path,
                params=params,
                json=body,
                headers=headers,
            )
    except httpx.HTTPError:
        return _error("service_unavailable", "The Cosmos data service is unavailable.")

    if response.status_code >= 400:
        if response.status_code in {401, 403}:
            return _error("forbidden", "The request is not authorized.")
        if response.status_code == 404:
            return _error("not_found", "The requested record was not found.")
        if response.status_code == 422:
            return _error("invalid_input", "The request contains an invalid value.")
        if response.status_code == 429:
            return _error("rate_limited", "The request limit has been reached.")
        if response.status_code == 503:
            return _error("feature_unavailable", "This capability is currently unavailable.")
        return _error(
            "service_unavailable", "The Cosmos data service could not complete the request."
        )

    try:
        result = response.json()
    except ValueError:
        return _error("invalid_response", "The Cosmos data service returned an invalid response.")
    try:
        result_size = len(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
    except (TypeError, ValueError):
        return _error("invalid_response", "The Cosmos data service returned an invalid response.")
    if result_size > MAX_TOOL_RESPONSE_BYTES:
        return _error("output_too_large", "The result exceeds the supported response size.")
    if not isinstance(result, dict):
        return _error("invalid_response", "The Cosmos data service returned an invalid response.")
    return result


def _date_params(
    start: date | None, end: date | None, start_name: str, end_name: str
) -> dict[str, str]:
    result: dict[str, str] = {}
    if start is not None:
        result[start_name] = start.isoformat()
    if end is not None:
        result[end_name] = end.isoformat()
    return result


@server.tool()
async def search_astronomy_records(
    ctx: Context,
    query: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Search stored APOD records by text and date, returning bounded provenance."""
    invalid = _validate_page(page, page_size) or _validate_window(start_date, end_date, 366)
    if invalid:
        return invalid
    if query is not None and (not query.strip() or len(query) > 200):
        return _error("invalid_input", "Query must contain between 1 and 200 characters.")
    params: dict[str, QueryParam] = {"page": page, "page_size": page_size}
    if query:
        params["q"] = query.strip()
    params.update(_date_params(start_date, end_date, "start_date", "end_date"))
    return await _api_request(ctx, "GET", "/api/v1/astronomy/records", params=params)


@server.tool()
async def get_astronomy_picture(ctx: Context, apod_date: date) -> dict[str, Any]:
    """Retrieve one APOD Basic item by date with provenance."""
    return await _api_request(ctx, "GET", f"/api/v1/astronomy/apod/{apod_date.isoformat()}")


@server.tool()
async def search_asteroids(
    ctx: Context,
    query: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    potentially_hazardous: bool | None = None,
    minimum_diameter_km: float | None = None,
    maximum_diameter_km: float | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Search the bounded NeoWs close-approach window and report units and coverage."""
    invalid = _validate_page(page, page_size) or _validate_window(start_date, end_date, 7)
    if invalid:
        return invalid
    if query is not None and len(query) > 100:
        return _error("invalid_input", "Query must not exceed 100 characters.")
    if minimum_diameter_km is not None and minimum_diameter_km < 0:
        return _error("invalid_input", "Minimum diameter cannot be negative.")
    if maximum_diameter_km is not None and maximum_diameter_km < 0:
        return _error("invalid_input", "Maximum diameter cannot be negative.")
    if (
        minimum_diameter_km is not None
        and maximum_diameter_km is not None
        and minimum_diameter_km > maximum_diameter_km
    ):
        return _error("invalid_input", "Minimum diameter must not exceed maximum diameter.")
    params: dict[str, QueryParam] = {"page": page, "page_size": page_size}
    if query:
        params["q"] = query.strip()
    if potentially_hazardous is not None:
        params["potentially_hazardous"] = potentially_hazardous
    if minimum_diameter_km is not None:
        params["minimum_diameter_km"] = minimum_diameter_km
    if maximum_diameter_km is not None:
        params["maximum_diameter_km"] = maximum_diameter_km
    params.update(_date_params(start_date, end_date, "close_approach_start", "close_approach_end"))
    return await _api_request(ctx, "GET", "/api/v1/asteroids", params=params)


@server.tool()
async def get_asteroid_details(ctx: Context, neo_id: str) -> dict[str, Any]:
    """Retrieve one NeoWs object; identifiers must contain 1 to 20 digits."""
    if not re.fullmatch(r"\d{1,20}", neo_id):
        return _error("invalid_input", "Asteroid IDs must contain 1 to 20 digits.")
    return await _api_request(ctx, "GET", f"/api/v1/asteroids/{neo_id}")


@server.tool()
async def compare_asteroids(ctx: Context, neo_ids: list[str]) -> dict[str, Any]:
    """Compare 2 to 10 asteroid records with explicit units and missing values."""
    if not 2 <= len(neo_ids) <= 10:
        return _error("invalid_input", "Provide between 2 and 10 asteroid IDs.")
    if len(set(neo_ids)) != len(neo_ids) or any(
        not re.fullmatch(r"\d{1,20}", item) for item in neo_ids
    ):
        return _error("invalid_input", "Asteroid IDs must be unique numeric identifiers.")
    return await _api_request(
        ctx,
        "POST",
        "/api/v1/asteroids/compare",
        body={"neo_ids": neo_ids},
        required_scope=READ_SCOPE,
    )


@server.tool()
async def search_space_weather_events(
    ctx: Context,
    event_types: list[str],
    start_date: date,
    end_date: date,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Search up to three DONKI event types over at most 30 days."""
    invalid = _validate_page(page, page_size) or _validate_window(start_date, end_date, 30)
    if invalid:
        return invalid
    if not 1 <= len(event_types) <= MAX_SPACE_WEATHER_TYPES:
        return _error("invalid_input", "Provide between 1 and 3 event types.")
    if any(event_type not in DONKI_TYPES for event_type in event_types):
        return _error("invalid_input", "One or more DONKI event types are unsupported.")
    results: list[dict[str, Any]] = []
    for event_type in event_types:
        response = await _api_request(
            ctx,
            "GET",
            "/api/v1/space-weather/events",
            params={
                "type": event_type,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": 1,
                "page_size": page_size,
            },
        )
        if "error" in response:
            return response
        items = response.get("items", [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    item.pop("details", None)
                    results.append(item)
    results.sort(key=lambda item: str(item.get("start_time") or ""), reverse=True)
    bounded = results[:page_size]
    return {
        "items": bounded,
        "page": page,
        "page_size": page_size,
        "total": len(results),
        "types_queried": event_types,
        "window": {"start": start_date.isoformat(), "end": end_date.isoformat(), "timezone": "UTC"},
    }


@server.tool()
async def get_space_weather_summary(
    ctx: Context,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """Summarize stored DONKI records; counts are not a severity index."""
    invalid = _validate_window(start_date, end_date, 30)
    if invalid:
        return invalid
    return await _api_request(
        ctx,
        "GET",
        "/api/v1/space-weather/summary",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
    )


@server.tool()
async def search_earth_events(
    ctx: Context,
    category: str | None = None,
    status: Literal["open", "closed", "all"] = "open",
    start_date: date | None = None,
    end_date: date | None = None,
    bbox: list[float] | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Search EONET curated metadata; results are not an exhaustive census."""
    invalid = _validate_page(page, page_size) or _validate_window(start_date, end_date, 366)
    if invalid:
        return invalid
    if status not in {"open", "closed", "all"}:
        return _error("invalid_input", "Status must be open, closed or all.")
    if category is not None and (not category.strip() or len(category) > 80):
        return _error("invalid_input", "Category must contain between 1 and 80 characters.")
    params: dict[str, QueryParam] = {"status": status, "page": page, "page_size": page_size}
    if category:
        params["category"] = category.strip()
    params.update(_date_params(start_date, end_date, "start", "end"))
    if bbox is not None:
        if len(bbox) != 4:
            return _error(
                "invalid_input",
                "Bounding box requires min longitude, min latitude, max longitude, max latitude.",
            )
        min_lon, max_lat, max_lon, min_lat = bbox
        if (
            not -180 <= min_lon <= 180
            or not -180 <= max_lon <= 180
            or not -90 <= min_lat <= 90
            or not -90 <= max_lat <= 90
            or min_lon > max_lon
            or max_lat < min_lat
        ):
            return _error(
                "invalid_input", "Bounding box coordinates are outside valid geographic bounds."
            )
        params["bbox"] = ",".join(str(value) for value in (min_lon, max_lat, max_lon, min_lat))
    return await _api_request(ctx, "GET", "/api/v1/earth-events", params=params)


@server.tool()
async def search_nasa_media(
    ctx: Context,
    query: str,
    media_type: Literal["image", "video", "audio"] | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Search NASA media metadata and links without fetching or copying assets."""
    invalid = _validate_page(page, page_size)
    if invalid:
        return invalid
    if not query.strip() or len(query) > 200:
        return _error("invalid_input", "Query must contain between 1 and 200 characters.")
    if year_start is not None and (year_start < 1900 or year_start > 2200):
        return _error("invalid_input", "Starting year must be between 1900 and 2200.")
    if year_end is not None and (year_end < 1900 or year_end > 2200):
        return _error("invalid_input", "Ending year must be between 1900 and 2200.")
    if year_start is not None and year_end is not None and year_start > year_end:
        return _error("invalid_input", "Starting year must not exceed ending year.")
    params: dict[str, QueryParam] = {"q": query.strip(), "page": page, "page_size": page_size}
    if media_type:
        params["media_type"] = media_type
    if year_start is not None:
        params["year_start"] = year_start
    if year_end is not None:
        params["year_end"] = year_end
    return await _api_request(ctx, "GET", "/api/v1/media", params=params)


@server.tool()
async def generate_scientific_report(ctx: Context, question: str) -> dict[str, Any]:
    """Request a user-owned scientific report; generation is policy-gated."""
    if not question.strip() or len(question) > 4000:
        return _error("invalid_input", "Question must contain between 1 and 4000 characters.")
    return await _api_request(
        ctx,
        "POST",
        "/api/v1/reports",
        body={"question": question.strip()},
        required_scope=REPORT_SCOPE,
    )


@server.resource("cosmos://catalog/sources", mime_type="application/json")
async def source_catalog() -> str:
    """List supported public sources and official service links."""
    return json.dumps(
        {
            "sources": [
                {
                    "code": "APOD",
                    "name": "Astronomy Picture of the Day",
                    "terms": "https://science.nasa.gov/",
                },
                {
                    "code": "NEOWS",
                    "name": "Near Earth Object Web Service",
                    "terms": "https://api.nasa.gov/",
                },
                {
                    "code": "DONKI",
                    "name": "Space Weather Database Of Notifications, Knowledge, Information",
                    "terms": "https://ccmc.gsfc.nasa.gov/DONKI/",
                },
                {
                    "code": "EONET",
                    "name": "Earth Observatory Natural Event Tracker",
                    "terms": "https://eonet.gsfc.nasa.gov/",
                },
                {
                    "code": "NASA_MEDIA",
                    "name": "NASA Image and Video Library",
                    "terms": "https://images.nasa.gov/",
                },
            ],
            "freshness": "Check each record's retrieved_at and provenance fields.",
        },
        ensure_ascii=False,
    )


@server.resource("cosmos://help/scientific-limitations", mime_type="text/markdown")
async def scientific_limitations() -> str:
    """Explain units, uncertainty, freshness and non-prediction limits."""
    return (
        "# Scientific data limitations\n\n"
        "- Values and classifications retain the meaning supplied by their source.\n"
        "- Missing measurements remain unknown; they are not estimated by this service.\n"
        "- Retrieval time and source links describe provenance, not a guarantee of freshness.\n"
        "- EONET is curated event metadata and is not an exhaustive census.\n"
        "- Asteroid measurements and hazard flags are not an impact prediction.\n"
        "- Space-weather event counts are not a severity index.\n"
        "- Generated scientific reports are disabled until policy and validation gates pass.\n"
    )


@server.resource("cosmos://records/{source}/{record_id}", mime_type="application/json")
async def read_public_record(source: str, record_id: str, ctx: Context) -> str:
    """Read one allowlisted public record by source and validated upstream identifier."""
    source_key = source.upper()
    if source_key == "APOD" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", record_id):
        path = f"/api/v1/astronomy/apod/{record_id}"
    elif source_key == "NEOWS" and re.fullmatch(r"\d{1,20}", record_id):
        path = f"/api/v1/asteroids/{record_id}"
    elif source_key == "DONKI" and re.fullmatch(
        r"[A-Za-z0-9_-]{1,40}:[A-Za-z0-9._:-]{1,255}", record_id
    ):
        if record_id.split(":", maxsplit=1)[0] not in DONKI_TYPES:
            return json.dumps(_error("invalid_input", "The DONKI event type is unsupported."))
        path = f"/api/v1/space-weather/events/{record_id}"
    elif source_key == "DONKI" and re.fullmatch(
        r"[A-Za-z0-9_-]{1,40}:[A-Za-z0-9._:-]{1,255}", record_id
    ):
        if record_id.split(":", maxsplit=1)[0] not in DONKI_TYPES:
            return json.dumps(_error("invalid_input", "The DONKI event type is unsupported."))
        path = f"/api/v1/space-weather/events/{record_id}"
    elif source_key == "EONET" and re.fullmatch(r"[A-Za-z0-9._-]{1,100}", record_id):
        path = f"/api/v1/earth-events/{record_id}"
    elif source_key == "NASA_MEDIA" and re.fullmatch(r"[A-Za-z0-9._-]{1,100}", record_id):
        path = f"/api/v1/media/{record_id}"
    else:
        return json.dumps(
            _error("invalid_input", "The source or record identifier is unsupported.")
        )
    result = await _api_request(ctx, "GET", path)
    return json.dumps(result, ensure_ascii=False, default=str)


@server.resource("cosmos://reports/{report_id}", mime_type="application/json")
async def read_owned_report(report_id: str, ctx: Context) -> str:
    """Read a report owned by the authenticated caller."""
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", report_id):
        return json.dumps(_error("invalid_input", "The report identifier is invalid."))
    result = await _api_request(
        ctx, "GET", f"/api/v1/reports/{report_id}", required_scope=READ_SCOPE
    )
    return json.dumps(result, ensure_ascii=False, default=str)


@server.prompt()
async def explain_scientific_record(
    source: str,
    record_id: str,
    audience: Literal["general", "student", "technical"] = "general",
) -> str:
    """Create a safe prompt for explaining one cited record."""
    return (
        f"Explain the {source} record {record_id} for a {audience} audience. "
        "Use only the record supplied by the host, cite its provenance, preserve unknowns, "
        "label any generated text, and avoid predictions or unsupported scientific claims."
    )


@server.prompt()
async def compare_scientific_records(record_ids: list[str], comparison_goal: str) -> str:
    """Create a prompt to compare explicitly aligned record fields."""
    if not 2 <= len(record_ids) <= 10 or len(comparison_goal) > 500:
        return (
            "Provide 2 to 10 record identifiers and a comparison goal no longer than 500 "
            "characters."
        )
    return (
        f"Compare these records: {', '.join(record_ids)}. Goal: {comparison_goal}. "
        "Align only equivalent fields and units, disclose missing values, cite provenance, "
        "and do not infer impact risk."
    )


@server.prompt()
async def draft_source_grounded_report(question: str, domain: str) -> str:
    """Create a gated prompt for a report grounded in retrieved evidence."""
    return (
        f"Draft a source-grounded report for domain {domain}. Question: {question}. "
        "Use only validated retrieved records, include observed facts and limitations separately, "
        "cite every material claim, abstain without adequate evidence, and label generated text. "
        "The server must still enforce research:generate scope and its policy gate."
    )


_mcp_asgi = server.streamable_http_app(
    transport_security=TransportSecuritySettings(
        allowed_hosts=sorted(
            {
                urlsplit(_resource_url).netloc,
                "localhost:8000",
                "127.0.0.1:8000",
                "mcp:8000",
            }
        )
    ),
    session_idle_timeout=900,
    max_sessions=500,
)


async def _health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "cosmos-mcp"})


@asynccontextmanager
async def _lifespan(_app: Starlette) -> AsyncIterator[None]:
    async with server.session_manager.run():
        yield


app = Starlette(
    routes=[
        Route("/health/live", _health, methods=["GET"]),
        Mount("/", app=_mcp_asgi),
    ],
    lifespan=_lifespan,
)
