"""NASA Image and Video Library search and metadata client."""

import re
from typing import Any

from pydantic import ValidationError

from app.clients.nasa_base import NASAClient
from app.core.errors import UpstreamError
from app.models.nasa import NASAImageSearchResponse


class NASAMediaClient:
    def __init__(self, transport: NASAClient, base_url: str) -> None:
        self.transport = transport
        self.base_url = base_url.rstrip("/")

    async def search(
        self,
        *,
        query: str | None = None,
        nasa_id: str | None = None,
        media_type: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        if not query and not nasa_id:
            raise ValueError("NASA media search requires a query or NASA ID.")
        if media_type and media_type not in {"image", "video", "audio"}:
            raise ValueError("NASA media type must be image, video, or audio.")
        if page < 1 or page_size < 1 or page_size > 100:
            raise ValueError(
                "NASA media page must be positive and page_size must be between 1 and 100."
            )
        if year_start is not None and year_end is not None and year_start > year_end:
            raise ValueError("year_start must be on or before year_end.")
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if query:
            params["q"] = query[:200]
        if nasa_id:
            params["nasa_id"] = nasa_id[:100]
        if media_type:
            params["media_type"] = media_type
        if year_start is not None:
            params["year_start"] = year_start
        if year_end is not None:
            params["year_end"] = year_end
        payload, _, _ = await self.transport.get_json(
            "NASA_MEDIA", f"{self.base_url}/search", params=params
        )
        try:
            NASAImageSearchResponse.model_validate(payload)
        except ValidationError as error:
            raise UpstreamError(
                "NASA_MEDIA",
                "upstream_schema_error",
                "NASA media search returned an unexpected envelope.",
                retryable=False,
            ) from error
        if not isinstance(payload, dict):
            raise UpstreamError(
                "NASA_MEDIA",
                "upstream_schema_error",
                "NASA media search returned an unexpected envelope.",
                retryable=False,
            )
        return payload

    async def asset_manifest(self, nasa_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", nasa_id):
            raise ValueError("NASA media identifier is invalid.")
        payload, _, _ = await self.transport.get_json(
            "NASA_MEDIA", f"{self.base_url}/asset/{nasa_id}"
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("collection"), dict):
            raise UpstreamError(
                "NASA_MEDIA",
                "upstream_schema_error",
                "NASA media asset manifest is malformed.",
                retryable=False,
            )
        return payload

    async def metadata(self, nasa_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", nasa_id):
            raise ValueError("NASA media identifier is invalid.")
        payload, _, _ = await self.transport.get_json(
            "NASA_MEDIA", f"{self.base_url}/metadata/{nasa_id}"
        )
        if not isinstance(payload, dict):
            raise UpstreamError(
                "NASA_MEDIA",
                "upstream_schema_error",
                "NASA media metadata response is malformed.",
                retryable=False,
            )
        return payload
