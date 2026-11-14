"""DONKI client using NASA CCMC's current API host."""

from datetime import date
from typing import Any

from app.clients.nasa_base import NASAClient
from app.core.errors import UpstreamError

DONKI_EVENT_TYPES = frozenset(
    {
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
    }
)
DONKI_OPTION_KEYS = {
    "CMEAnalysis": frozenset({"mostAccurateOnly", "speed", "halfAngle", "catalog"}),
    "IPS": frozenset({"location", "catalog"}),
    "notifications": frozenset({"type"}),
}
NASA_API_DONKI_FALLBACK_BASE_URL = "https://api.nasa.gov/DONKI"


class DONKIClient:
    def __init__(
        self,
        transport: NASAClient,
        base_url: str,
        fallback_base_url: str = NASA_API_DONKI_FALLBACK_BASE_URL,
    ) -> None:
        self.transport = transport
        self.base_url = base_url.rstrip("/")
        self.fallback_base_url = fallback_base_url.rstrip("/")

    async def events(
        self,
        event_type: str,
        start_date: date,
        end_date: date,
        *,
        options: dict[str, str | int | float | bool] | None = None,
    ) -> list[dict[str, Any]]:
        if event_type not in DONKI_EVENT_TYPES:
            raise ValueError("Unsupported DONKI event type.")
        if end_date < start_date or (end_date - start_date).days > 30:
            raise ValueError("DONKI date window must be ordered and at most 30 days.")
        params: dict[str, Any] = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }
        if options:
            allowed_options = DONKI_OPTION_KEYS.get(event_type, frozenset())
            if not set(options) <= allowed_options:
                raise ValueError(
                    "DONKI options include an unsupported parameter for this event type."
                )
            params.update(options)
        try:
            payload, _, _ = await self.transport.get_json(
                "DONKI",
                f"{self.base_url}/{event_type}",
                params=params,
                use_api_key=True,
                max_retries=0,
            )
        except UpstreamError as primary_error:
            if not primary_error.retryable or primary_error.code == "upstream_rate_limited":
                raise
            payload, _, _ = await self.transport.get_json(
                "DONKI",
                f"{self.fallback_base_url}/{event_type}",
                params=params,
                use_api_key=True,
                max_retries=min(1, self.transport.max_retries),
            )
        if isinstance(payload, list):
            if all(isinstance(record, dict) for record in payload):
                return payload
        if event_type == "notifications" and isinstance(payload, dict):
            notifications = payload.get("notifications")
            if isinstance(notifications, list):
                if all(isinstance(record, dict) for record in notifications):
                    return notifications
        raise UpstreamError(
            "DONKI",
            "upstream_schema_error",
            "DONKI returned an unexpected event list.",
            retryable=False,
        )
