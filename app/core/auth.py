"""Provider-neutral OIDC token validation and local-only development identity."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlsplit

import httpx
import jwt
from fastapi import Depends, Request
from jwt import PyJWKClient

from app.core.config import Settings, get_settings
from app.core.errors import AppError, FeatureUnavailableError


@dataclass(frozen=True, slots=True)
class UserContext:
    subject: str
    scopes: frozenset[str]
    roles: frozenset[str]
    is_development_identity: bool = False


@lru_cache(maxsize=8)
def _jwks_client(issuer_url: str) -> PyJWKClient:
    issuer = issuer_url.rstrip("/")
    discovery_url = f"{issuer}/.well-known/openid-configuration"
    with httpx.Client(timeout=httpx.Timeout(5.0, connect=3.0), follow_redirects=False) as client:
        response = client.get(discovery_url)
        response.raise_for_status()
        metadata = response.json()

    if not isinstance(metadata, dict) or str(metadata.get("issuer", "")).rstrip("/") != issuer:
        raise ValueError("OIDC discovery issuer does not match the configured issuer.")

    jwks_uri = metadata.get("jwks_uri")
    if not isinstance(jwks_uri, str):
        raise ValueError("OIDC discovery document does not provide a JWKS URI.")
    parsed_jwks_uri = urlsplit(jwks_uri)
    if parsed_jwks_uri.scheme != "https" or not parsed_jwks_uri.netloc:
        raise ValueError("OIDC JWKS URI must use HTTPS.")
    return PyJWKClient(jwks_uri, cache_jwk_set=True, timeout=5)


def _decode_access_token(token: str, issuer_url: str, audience: str) -> UserContext:
    client = _jwks_client(issuer_url)
    signing_key = client.get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256", "ES256"],
        issuer=issuer_url.rstrip("/"),
        audience=audience,
        options={"require": ["exp", "iat", "sub"]},
        leeway=30,
    )
    raw_scopes = claims.get("scope", "")
    scopes = set(raw_scopes.split()) if isinstance(raw_scopes, str) else set(raw_scopes or [])
    roles = claims.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]
    return UserContext(
        str(claims["sub"]), frozenset(scopes), frozenset(str(role) for role in roles)
    )


async def get_optional_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> UserContext | None:
    authorization = request.headers.get("authorization", "")
    if authorization.startswith("Bearer "):
        if not settings.oidc_issuer_url or not settings.oidc_audience:
            raise FeatureUnavailableError(
                "identity_unconfigured", "Identity provider is not configured."
            )
        token = authorization[7:].strip()
        if not token:
            raise AppError(
                "invalid_token", "Unauthorized", "A valid access token is required.", 401
            )
        try:
            return await asyncio.to_thread(
                _decode_access_token,
                token,
                settings.oidc_issuer_url,
                settings.oidc_audience,
            )
        except Exception:
            # Deliberately avoid returning provider/JWKS/token details to callers.
            raise AppError(
                "invalid_token", "Unauthorized", "The access token is invalid or expired.", 401
            ) from None

    if settings.app_env == "development" and settings.dev_auth_enabled:
        subject = request.headers.get("x-dev-user", "local-developer")
        if not re.fullmatch(r"[A-Za-z0-9._@-]{1,128}", subject):
            raise AppError(
                "invalid_dev_identity",
                "Unauthorized",
                "The local development identity is invalid.",
                401,
            )
        return UserContext(subject, frozenset({"research:generate"}), frozenset(), True)
    return None


async def require_user(user: UserContext | None = Depends(get_optional_user)) -> UserContext:
    if user is None:
        raise AppError(
            "authentication_required", "Unauthorized", "Authentication is required.", 401
        )
    return user


async def require_scope(scope: str, user: UserContext = Depends(require_user)) -> UserContext:
    if scope not in user.scopes and "cosmos_admin" not in user.roles:
        raise AppError("forbidden", "Forbidden", "The requested operation is not authorized.", 403)
    return user


async def require_admin(user: UserContext = Depends(require_user)) -> UserContext:
    if "cosmos_admin" not in user.roles:
        raise AppError("forbidden", "Forbidden", "Administrative access is required.", 403)
    return user
