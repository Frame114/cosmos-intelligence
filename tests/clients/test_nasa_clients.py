"""Contract-level checks for NASA adapters using isolated mock HTTP transports."""

from __future__ import annotations

import asyncio
from datetime import date

import httpx
import pytest

from app.clients.nasa_apod import NasaApodClient
from app.clients.nasa_base import NASAClient
from app.clients.nasa_donki import DONKIClient
from app.clients.nasa_eonet import EONETClient
from app.clients.nasa_media import NASAMediaClient
from app.clients.nasa_neows import NeoWsClient
from app.core.errors import UpstreamError


def _mock_client(
    responses: list[httpx.Response],
) -> tuple[httpx.AsyncClient, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        index = min(len(requests) - 1, len(responses) - 1)
        return responses[index]

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), requests


def test_apod_uses_basic_guide_date_codes_and_page_bound() -> None:
    async def scenario() -> None:
        client, requests = _mock_client(
            [
                httpx.Response(
                    200,
                    json=[
                        {
                            "date": "2026-11-13",
                            "post_id": 12,
                            "title": "A quiet galaxy",
                            "media_type": "image",
                            "explanation": "A fixture description.",
                            "url": "https://images.nasa.gov/example.jpg",
                        }
                    ],
                )
            ]
        )
        try:
            transport = NASAClient(client, max_retries=0, api_key="test-only-key")
            adapter = NasaApodClient(transport, "https://science.nasa.gov/wp-json/wp/v2/apod-basic")
            records = await adapter.search(
                start_date=date(2026, 11, 13), end_date=date(2026, 11, 13), page_size=1
            )
            assert records[0].date == date(2026, 11, 13)
            assert requests[0].url.params["date_from"] == "261113"
            assert requests[0].url.params["date_to"] == "261113"
            assert requests[0].url.params["per_page"] == "1"
            assert "api_key" not in requests[0].url.params
            with pytest.raises(ValueError):
                await adapter.search(page_size=26)
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_neows_uses_nasa_key_and_bounded_feed_window() -> None:
    async def scenario() -> None:
        client, requests = _mock_client([httpx.Response(200, json={"near_earth_objects": {}})])
        try:
            transport = NASAClient(client, max_retries=0, api_key="test-only-key")
            adapter = NeoWsClient(transport, "https://api.nasa.gov/neo/rest/v1")
            await adapter.feed(date(2026, 11, 13), date(2026, 11, 20))
            assert requests[0].url.params["api_key"] == "test-only-key"
            assert requests[0].url.params["start_date"] == "2026-11-13"
            with pytest.raises(ValueError):
                await adapter.feed(date(2026, 11, 13), date(2026, 11, 21))
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_donki_uses_current_ccmc_host_contract_and_rejects_bad_options() -> None:
    async def scenario() -> None:
        client, requests = _mock_client([httpx.Response(200, json=[{"activityID": "CME-1"}])])
        try:
            transport = NASAClient(client, max_retries=0, api_key="test-only-key")
            adapter = DONKIClient(transport, "https://ccmc.gsfc.nasa.gov/DONKI-API/get")
            events = await adapter.events("CME", date(2026, 11, 1), date(2026, 11, 13))
            assert events[0]["activityID"] == "CME-1"
            assert requests[0].url.path.endswith("/CME")
            assert requests[0].url.params["startDate"] == "2026-11-01"
            assert requests[0].url.params["api_key"] == "test-only-key"
            with pytest.raises(ValueError):
                await adapter.events(
                    "CME", date(2026, 11, 1), date(2026, 11, 13), options={"unknown": "value"}
                )
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_eonet_preserves_documented_bbox_order_and_geometry_magnitude() -> None:
    async def scenario() -> None:
        event_payload = {
            "id": "EONET_123",
            "title": "Volcano",
            "geometry": [
                {
                    "date": "2026-11-13T00:00:00Z",
                    "type": "Point",
                    "coordinates": [20.0, 10.0],
                    "magnitudeValue": 3.5,
                    "magnitudeUnit": "VEI",
                }
            ],
        }
        client, requests = _mock_client(
            [httpx.Response(200, json={"events": []}), httpx.Response(200, json=event_payload)]
        )
        try:
            transport = NASAClient(client, max_retries=0)
            adapter = EONETClient(transport, "https://eonet.gsfc.nasa.gov/api/v3")
            await adapter.events(bbox=(-10.0, 45.0, 20.0, -15.0))
            event = await adapter.get("EONET_123")
            assert requests[0].url.params["bbox"] == "-10.0,45.0,20.0,-15.0"
            assert event.geometry[0].magnitudeValue == 3.5
            with pytest.raises(ValueError):
                await adapter.get("../outside")
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_media_search_validates_envelope_and_requires_a_query() -> None:
    async def scenario() -> None:
        client, requests = _mock_client(
            [
                httpx.Response(
                    200,
                    json={
                        "collection": {
                            "items": [
                                {"data": [{"nasa_id": "ABC-1", "title": "Moon"}], "links": []}
                            ],
                            "metadata": {"total_hits": 1},
                            "links": [],
                        }
                    },
                )
            ]
        )
        try:
            transport = NASAClient(client, max_retries=0)
            adapter = NASAMediaClient(transport, "https://images-api.nasa.gov")
            response = await adapter.search(query="moon", media_type="image", page_size=10)
            assert response["collection"]["items"][0]["data"][0]["nasa_id"] == "ABC-1"
            assert requests[0].url.params["q"] == "moon"
            with pytest.raises(ValueError):
                await adapter.search()
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_base_transport_bounds_retries_and_never_returns_upstream_error_body() -> None:
    async def scenario() -> None:
        client, requests = _mock_client(
            [
                httpx.Response(503, headers={"Retry-After": "0"}, text="temporarily down"),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        try:
            transport = NASAClient(client, max_retries=1, api_key="test-only-key")
            payload, _, _ = await transport.get_json(
                "NEOWS", "https://api.nasa.gov/neo/rest/v1/feed", use_api_key=True
            )
            assert payload == {"ok": True}
            assert len(requests) == 2
        finally:
            await client.aclose()

        error_client, _ = _mock_client([httpx.Response(401, json={"message": "test-only-key"})])
        try:
            transport = NASAClient(error_client, max_retries=0, api_key="test-only-key")
            with pytest.raises(UpstreamError) as raised:
                await transport.get_json(
                    "NEOWS", "https://api.nasa.gov/neo/rest/v1/feed", use_api_key=True
                )
            assert "test-only-key" not in str(raised.value)
            assert "test-only-key" not in repr(raised.value)
        finally:
            await error_client.aclose()

    asyncio.run(scenario())


def test_base_transport_stops_reading_an_oversized_body() -> None:
    async def scenario() -> None:
        client, _ = _mock_client([httpx.Response(200, content=b"x" * 512)])
        try:
            transport = NASAClient(client, max_retries=0, max_response_bytes=32)
            with pytest.raises(UpstreamError) as raised:
                await transport.get_json("APOD", "https://science.nasa.gov/api")
            assert raised.value.code == "upstream_response_too_large"
        finally:
            await client.aclose()

    asyncio.run(scenario())
