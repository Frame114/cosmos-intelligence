"""Shared NASA HTTP transport with bounded retries and redacted diagnostics."""

from __future__ import annotations

import asyncio
import email.utils
import json
import random
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.errors import UpstreamError

TRANSIENT_STATUSES = {429, 500, 502, 503, 504}


class NASAClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        max_retries: int = 3,
        max_response_bytes: int = 8_000_000,
        api_key: str = "",
    ) -> None:
        if max_retries < 0 or max_retries > 5:
            raise ValueError("max_retries must be between 0 and 5.")
        if max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive.")
        self.http_client = http_client
        self.max_retries = max_retries
        self.max_response_bytes = max_response_bytes
        self.api_key = api_key

    async def get_json(
        self,
        source: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        use_api_key: bool = False,
        max_retries: int | None = None,
    ) -> tuple[Any, datetime, dict[str, str]]:
        request_params = dict(params or {})
        if use_api_key and self.api_key:
            request_params["api_key"] = self.api_key

        retry_limit = self.max_retries if max_retries is None else max_retries
        if retry_limit < 0 or retry_limit > self.max_retries:
            raise ValueError("max_retries override must be between zero and the configured limit.")

        for attempt in range(retry_limit + 1):
            try:
                async with self.http_client.stream("GET", url, params=request_params) as response:
                    if response.status_code in TRANSIENT_STATUSES and attempt < retry_limit:
                        retry_after = self._retry_after(response.headers.get("Retry-After"))
                        await asyncio.sleep(
                            retry_after if retry_after is not None else self._backoff(attempt)
                        )
                        continue
                    if response.status_code >= 400:
                        status = 429 if response.status_code == 429 else 502
                        code = (
                            "upstream_rate_limited"
                            if response.status_code == 429
                            else "upstream_http_error"
                        )
                        raise UpstreamError(
                            source,
                            code,
                            "The upstream data source rejected or failed the request.",
                            status_code=status,
                            retryable=response.status_code in TRANSIENT_STATUSES,
                        )

                    content_length = response.headers.get("Content-Length")
                    if content_length and content_length.isdigit():
                        if int(content_length) > self.max_response_bytes:
                            raise self._too_large(source)

                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > self.max_response_bytes:
                            raise self._too_large(source)

                    try:
                        payload = json.loads(body)
                    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
                        raise UpstreamError(
                            source,
                            "upstream_invalid_json",
                        "The upstream source returned invalid JSON.",
                            status_code=502,
                            retryable=False,
                        ) from error

                    safe_headers = {
                        key.lower(): value
                        for key, value in response.headers.items()
                        if key.lower()
                        in {
                            "x-ratelimit-limit",
                            "x-ratelimit-remaining",
                            "retry-after",
                            "etag",
                            "last-modified",
                        }
                    }
                    return payload, datetime.now(UTC), safe_headers
            except httpx.TransportError as error:
                if attempt >= retry_limit:
                    raise UpstreamError(
                        source,
                        "upstream_timeout",
                        "The upstream data source did not respond.",
                        status_code=504,
                    ) from error
                await asyncio.sleep(self._backoff(attempt))
                continue

        raise UpstreamError(source, "upstream_unavailable")

    @staticmethod
    def _too_large(source: str) -> UpstreamError:
        return UpstreamError(
            source,
            "upstream_response_too_large",
            "The upstream response exceeded the configured size limit.",
            status_code=502,
            retryable=False,
        )

    @staticmethod
    def _backoff(attempt: int) -> float:
        return random.uniform(0.1, min(5.0, 0.5 * (2**attempt)))

    @staticmethod
    def _retry_after(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return max(0.0, min(30.0, float(value)))
        except ValueError:
            try:
                parsed = email.utils.parsedate_to_datetime(value)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
                return max(0.0, min(30.0, (parsed - datetime.now(UTC)).total_seconds()))
            except (TypeError, ValueError, OverflowError):
                return None
