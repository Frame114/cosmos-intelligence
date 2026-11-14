"""FastAPI application factory, lifecycle, health checks, and safe errors."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.private import admin_router as admin_api_router
from app.api.v1.private import router as private_api_router
from app.api.v1.public import router as public_api_router
from app.clients.gdelt import GDELTClient
from app.clients.jpl_ssd import JPLSmallBodyClient
from app.clients.nasa_apod import NasaApodClient
from app.clients.nasa_base import NASAClient
from app.clients.nasa_donki import DONKIClient
from app.clients.nasa_eonet import EONETClient
from app.clients.nasa_media import NASAMediaClient
from app.clients.nasa_neows import NeoWsClient
from app.clients.registry import NASAClients
from app.core.config import Settings, get_settings
from app.core.errors import AppError, FeatureUnavailableError
from app.core.middleware import RequestIdMiddleware
from app.db.session import create_engine, get_sessionmaker

EXPECTED_SCHEMA_REVISION = "20261114_0002"
_logger = logging.getLogger("cosmos.api")


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unavailable"))


def _problem_response(
    request: Request,
    *,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    retryable: bool = False,
    upstream: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "code": code,
        "request_id": _request_id(request),
        "retryable": retryable,
    }
    if upstream:
        body["upstream"] = upstream
    response_headers = {"X-Request-ID": _request_id(request)}
    if headers:
        response_headers.update(headers)
    return JSONResponse(
        body,
        status_code=status_code,
        media_type="application/problem+json",
        headers=response_headers,
    )


def _make_lifespan(
    settings_override: Settings | None,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        settings = settings_override or get_settings()
        application.state.settings = settings
        api_key = settings.nasa_api_key_value
        database_url = settings.database_url_value

        engine = None
        if database_url:
            engine_options: dict[str, object] = {}
            if database_url.startswith("postgresql+asyncpg://"):
                engine_options["pool_size"] = settings.db_pool_size
                engine_options["max_overflow"] = settings.db_pool_size
            engine = create_engine(database_url, **engine_options)
            application.state.db_engine = engine
            application.state.db_sessions = get_sessionmaker(engine)

        timeout = httpx.Timeout(settings.nasa_api_timeout_seconds, connect=5.0)
        http_client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(
                max_connections=settings.nasa_max_concurrency,
                max_keepalive_connections=settings.nasa_max_concurrency,
            ),
            follow_redirects=False,
        )
        application.state.nasa_http_client = http_client
        transport = NASAClient(
            http_client,
            max_retries=settings.nasa_max_retries,
            max_response_bytes=settings.nasa_max_response_bytes,
            api_key=api_key,
        )
        application.state.nasa_clients = NASAClients(
            apod=NasaApodClient(transport, settings.apod_base_url),
            neows=NeoWsClient(transport, settings.neows_base_url),
            donki=DONKIClient(transport, settings.donki_base_url),
            eonet=EONETClient(transport, settings.eonet_base_url),
            media=NASAMediaClient(transport, settings.nasa_media_base_url),
            jpl=JPLSmallBodyClient(
                transport, settings.jpl_ssd_base_url, settings.jpl_horizons_base_url
            ),
            gdelt=GDELTClient(transport),
        )

        try:
            yield
        finally:
            await http_client.aclose()
            if engine is not None:
                await engine.dispose()

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an API instance with optional settings injection for isolated tests."""

    resolved_settings = settings or get_settings()
    application = FastAPI(
        title="Cosmos Intelligence API",
        description="Scientific data integration and intelligence platform.",
        version="0.1.0",
        docs_url=None if resolved_settings.app_env == "production" else "/docs",
        redoc_url=None if resolved_settings.app_env == "production" else "/redoc",
        openapi_url=None if resolved_settings.app_env == "production" else "/openapi.json",
        lifespan=_make_lifespan(resolved_settings),
    )
    application.dependency_overrides[get_settings] = lambda: resolved_settings
    application.add_middleware(RequestIdMiddleware)
    application.include_router(public_api_router)
    application.include_router(private_api_router)
    application.include_router(admin_api_router)
    if resolved_settings.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=resolved_settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )

    if resolved_settings.app_env != "production":

        @application.get("/api/v1/openapi.json", include_in_schema=False)
        async def versioned_openapi() -> dict[str, Any]:
            return application.openapi()

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
        retry_after = (error.extra or {}).get("retry_after")
        headers = {"Retry-After": str(retry_after)} if isinstance(retry_after, int) else None
        return _problem_response(
            request,
            status_code=error.status_code,
            title=error.title,
            detail=error.detail,
            code=error.code,
            retryable=error.retryable,
            upstream=error.upstream,
            headers=headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, _error: RequestValidationError
    ) -> JSONResponse:
        return _problem_response(
            request,
            status_code=422,
            title="Invalid request",
            detail="The request contains one or more invalid fields.",
            code="validation_error",
        )

    @application.exception_handler(HTTPException)
    async def http_error_handler(request: Request, error: HTTPException) -> JSONResponse:
        safe_responses = {
            401: ("Unauthorized", "Authentication is required.", "authentication_required"),
            403: ("Forbidden", "The request is not authorized.", "forbidden"),
            404: ("Not found", "The requested resource was not found.", "not_found"),
            405: (
                "Method not allowed",
                "The request method is not supported.",
                "method_not_allowed",
            ),
        }
        title, detail, code = safe_responses.get(
            error.status_code,
            ("Request failed", "The request could not be completed.", "http_error"),
        )
        return _problem_response(
            request,
            status_code=error.status_code,
            title=title,
            detail=detail,
            code=code,
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
        # Log only safe metadata; exception messages can contain SQL, URLs, or credentials.
        _logger.error(
            "Unhandled request failure",
            extra={"request_id": _request_id(request), "error_type": type(error).__name__},
        )
        return _problem_response(
            request,
            status_code=500,
            title="Internal server error",
            detail="The request could not be completed.",
            code="internal_error",
        )

    @application.get("/health/live", tags=["operations"])
    @application.get("/health", tags=["operations"], include_in_schema=False)
    async def liveness() -> dict[str, str]:
        """Return a process-only liveness response."""

        return {"status": "ok", "service": "cosmos-intelligence"}

    @application.get("/health/ready", tags=["operations"])
    async def readiness(request: Request) -> dict[str, str]:
        """Return ready only when PostgreSQL is reachable and at the expected revision."""

        engine = getattr(request.app.state, "db_engine", None)
        if engine is None:
            raise FeatureUnavailableError(
                "database_unconfigured", "The database is not configured."
            )
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                result = await connection.execute(text("SELECT version_num FROM alembic_version"))
                revision = result.scalar_one_or_none()
        except SQLAlchemyError:
            raise FeatureUnavailableError(
                "database_not_ready", "The database is unavailable or has not been migrated."
            ) from None
        if revision != EXPECTED_SCHEMA_REVISION:
            raise FeatureUnavailableError(
                "database_schema_not_ready", "The database schema is not at the required revision."
            )
        return {"status": "ok", "database": "ready"}

    return application


app = create_app()
