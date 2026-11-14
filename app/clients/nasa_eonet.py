"""EONET v3 curated natural-event client."""

import re
from datetime import date
from typing import Any

from pydantic import ValidationError

from app.clients.nasa_base import NASAClient
from app.core.errors import UpstreamError
from app.models.nasa import EONETEvent


class EONETClient:
    def __init__(self, transport: NASAClient, base_url: str) -> None:
        self.transport = transport
        self.base_url = base_url.rstrip("/")

    async def events(
        self,
        *,
        category: str | None = None,
        status: str = "open",
        start_date: date | None = None,
        end_date: date | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        limit: int = 50,
        days: int | None = None,
    ) -> dict[str, Any]:
        if status not in {"open", "closed", "all"}:
            raise ValueError("EONET status must be open, closed, or all.")
        if not 1 <= limit <= 1000:
            raise ValueError("EONET limit must be between 1 and 1000.")
        if start_date and end_date and start_date > end_date:
            raise ValueError("EONET start date must be on or before end date.")
        params: dict[str, Any] = {"status": status, "limit": limit}
        if category:
            params["category"] = category
        if start_date:
            params["start"] = start_date.isoformat()
        if end_date:
            params["end"] = end_date.isoformat()
        if days is not None:
            if days < 1 or days > 3650:
                raise ValueError("EONET days must be between 1 and 3650.")
            params["days"] = days
        if bbox is not None:
            min_lon, max_lat, max_lon, min_lat = bbox
            if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
                raise ValueError("EONET longitude must be between -180 and 180.")
            if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
                raise ValueError("EONET latitude must be between -90 and 90.")
            if min_lon > max_lon or max_lat < min_lat:
                raise ValueError("EONET bounding box coordinates are inverted.")
            # EONET expects upper-left (min longitude, max latitude), then lower-right.
            params["bbox"] = ",".join(str(value) for value in bbox)
        payload, _, _ = await self.transport.get_json(
            "EONET", f"{self.base_url}/events", params=params
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
            raise UpstreamError(
                "EONET",
                "upstream_schema_error",
                "EONET returned an unexpected events envelope.",
                retryable=False,
            )
        return payload

    async def get(self, event_id: str) -> EONETEvent:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", event_id):
            raise ValueError("event_id is invalid.")
        payload, _, _ = await self.transport.get_json("EONET", f"{self.base_url}/events/{event_id}")
        try:
            return EONETEvent.model_validate(payload)
        except ValidationError as error:
            raise UpstreamError(
                "EONET",
                "upstream_schema_error",
                "EONET returned a malformed event.",
                retryable=False,
            ) from error

    async def layers(self, category_id: str) -> list[dict[str, Any]]:
        """Return the NASA imagery layers associated with an EONET category."""
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", category_id):
            raise ValueError("EONET category ID is invalid.")
        payload, _, _ = await self.transport.get_json(
            "EONET", f"{self.base_url}/layers/{category_id}"
        )
        categories = payload.get("categories") if isinstance(payload, dict) else None
        if not isinstance(categories, list):
            raise UpstreamError(
                "EONET",
                "upstream_schema_error",
                "EONET returned an unexpected imagery-layer envelope.",
                retryable=False,
            )
        for category in categories:
            layers = category.get("layers") if isinstance(category, dict) else None
            if isinstance(layers, list):
                return [layer for layer in layers if isinstance(layer, dict)]
        return []
