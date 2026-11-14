"""APOD Basic client using NASA's current replacement feed."""

from datetime import date

from pydantic import ValidationError

from app.clients.nasa_base import NASAClient
from app.core.errors import UpstreamError
from app.models.apod import ApodRecord


class NasaApodClient:
    def __init__(self, transport: NASAClient, base_url: str) -> None:
        self.transport = transport
        self.base_url = base_url.rstrip("/")

    async def get_latest(self) -> ApodRecord:
        records = await self.search(page=1, page_size=1)
        if not records:
            raise UpstreamError(
                "APOD", "upstream_empty", "NASA APOD returned no records.", retryable=False
            )
        return records[0]

    async def get_by_date(self, apod_date: date) -> ApodRecord | None:
        date_code = apod_date.strftime("%y%m%d")
        payload, _, _ = await self.transport.get_json("APOD", f"{self.base_url}/{date_code}")
        if not isinstance(payload, dict):
            raise UpstreamError(
                "APOD",
                "upstream_schema_error",
                "NASA APOD returned an unexpected record.",
                retryable=False,
            )
        return ApodRecord.model_validate(payload)

    async def search(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[ApodRecord]:
        if page < 1 or page_size < 1 or page_size > 25:
            raise ValueError("APOD page must be positive and page_size must be between 1 and 25.")
        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date must be on or before end_date.")
        params: dict[str, int | str] = {"page": page, "per_page": page_size}
        if start_date:
            params["date_from"] = start_date.strftime("%y%m%d")
        if end_date:
            params["date_to"] = end_date.strftime("%y%m%d")
        payload, _, _ = await self.transport.get_json("APOD", self.base_url, params=params)
        if not isinstance(payload, list):
            raise UpstreamError(
                "APOD",
                "upstream_schema_error",
                "NASA APOD returned an unexpected list.",
                retryable=False,
            )
        try:
            return [ApodRecord.model_validate(item) for item in payload]
        except ValidationError as error:
            raise UpstreamError(
                "APOD",
                "upstream_schema_error",
                "NASA APOD returned a malformed record.",
                retryable=False,
            ) from error
