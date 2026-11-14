"""Near-Earth Object Web Service client."""

from datetime import date
from typing import Any

from pydantic import ValidationError

from app.clients.nasa_base import NASAClient
from app.core.errors import UpstreamError
from app.models.nasa import NeoObject


class NeoWsClient:
    def __init__(self, transport: NASAClient, base_url: str) -> None:
        self.transport = transport
        self.base_url = base_url.rstrip("/")

    async def feed(self, start_date: date, end_date: date | None = None) -> dict[str, Any]:
        end = end_date or start_date
        if end < start_date or (end - start_date).days > 7:
            raise ValueError("NeoWs feed range must be ordered and at most seven days.")
        payload, _, _ = await self.transport.get_json(
            "NEOWS",
            f"{self.base_url}/feed",
            params={"start_date": start_date.isoformat(), "end_date": end.isoformat()},
            use_api_key=True,
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("near_earth_objects"), dict):
            raise UpstreamError(
                "NEOWS",
                "upstream_schema_error",
                "NeoWs returned an unexpected feed.",
                retryable=False,
            )
        return payload

    async def get(self, asteroid_id: str) -> NeoObject:
        if not asteroid_id.isdigit() or not 1 <= len(asteroid_id) <= 20:
            raise ValueError("asteroid_id must contain 1 to 20 digits.")
        payload, _, _ = await self.transport.get_json(
            "NEOWS",
            f"{self.base_url}/neo/{asteroid_id}",
            use_api_key=True,
        )
        try:
            return NeoObject.model_validate(payload)
        except ValidationError as error:
            raise UpstreamError(
                "NEOWS",
                "upstream_schema_error",
                "NeoWs returned a malformed asteroid record.",
                retryable=False,
            ) from error

    async def browse(self, page: int = 0, size: int = 20) -> dict[str, Any]:
        if page < 0 or size < 1 or size > 100:
            raise ValueError(
                "NeoWs browse page must be nonnegative and size must be between 1 and 100."
            )
        payload, _, _ = await self.transport.get_json(
            "NEOWS",
            f"{self.base_url}/neo/browse",
            params={"page": page, "size": size},
            use_api_key=True,
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("near_earth_objects"), list):
            raise UpstreamError(
                "NEOWS",
                "upstream_schema_error",
                "NeoWs returned an unexpected browse response.",
                retryable=False,
            )
        return payload
