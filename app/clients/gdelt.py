"""Cached, paced access to the public GDELT DOC 2.0 news search API."""

from __future__ import annotations

import asyncio
import re
from time import monotonic
from typing import Any

from app.clients.nasa_base import NASAClient
from app.core.errors import UpstreamError


class GDELTClient:
    """Search recent global news while respecting GDELT's low request rate."""

    def __init__(self, transport: NASAClient) -> None:
        self.transport = transport
        self._lock = asyncio.Lock()
        self._last_request_at = 0.0
        self._cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    async def search(
        self,
        query: str,
        *,
        exact_phrase: bool = True,
        max_records: int = 6,
    ) -> list[dict[str, Any]]:
        query_text = re.sub(r"\s+", " ", query).strip()
        if not query_text or len(query_text) > 240 or not 1 <= max_records <= 10:
            raise ValueError("GDELT search needs a query and at most 10 records.")
        request_query = f'"{query_text}"' if exact_phrase else query_text
        cache_key = request_query.casefold()
        cached = self._cache.get(cache_key)
        if cached and cached[0] > monotonic():
            return cached[1]

        async with self._lock:
            cached = self._cache.get(cache_key)
            if cached and cached[0] > monotonic():
                return cached[1]
            wait_seconds = 5.0 - (monotonic() - self._last_request_at)
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._last_request_at = monotonic()
            payload, _, _ = await self.transport.get_json(
                "GDELT",
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params={
                    "query": request_query,
                    "mode": "ArtList",
                    "format": "json",
                    "maxrecords": max_records,
                    "timespan": "3m",
                    "sort": "DateDesc",
                },
                max_retries=0,
            )
            articles = payload.get("articles") if isinstance(payload, dict) else None
            if articles is not None and not isinstance(articles, list):
                raise UpstreamError(
                    "GDELT",
                    "upstream_schema_error",
                    "GDELT returned an unexpected news-search response.",
                    retryable=False,
                )
            normalized = [
                self._article(item) for item in (articles or []) if isinstance(item, dict)
            ]
            self._cache[cache_key] = (monotonic() + 900, normalized)
            if len(self._cache) > 256:
                self._cache = {
                    key: value for key, value in self._cache.items() if value[0] > monotonic()
                }
            return normalized

    @staticmethod
    def _article(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": str(item.get("title") or "Untitled report")[:500],
            "url": item.get("url") if isinstance(item.get("url"), str) else None,
            "image_url": (
                item.get("socialimage") if isinstance(item.get("socialimage"), str) else None
            ),
            "publisher": str(item.get("domain") or "News source")[:200],
            "published_at": str(item.get("seendate") or "")[:40] or None,
            "language": str(item.get("language") or "")[:30] or None,
        }
