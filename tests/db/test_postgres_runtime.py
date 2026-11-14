"""Disposable PostgreSQL smoke test, enabled with COSMOS_TEST_DATABASE_URL."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_nasa_clients
from app.clients.registry import NASAClients
from app.core.config import Settings
from app.db.dependencies import get_db_session
from app.main import create_app
from app.models.apod import ApodRecord

TEST_DATABASE_URL = os.environ.get("COSMOS_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="No disposable PostgreSQL URL configured."
)


def _test_application() -> FastAPI:
    settings = Settings(_env_file=None, app_env="test", database_url=TEST_DATABASE_URL)
    application = create_app(settings)

    @application.get("/_integration/source-count")
    async def source_count(
        source_code: str,
        external_id: str,
        session: AsyncSession = Depends(get_db_session),
    ) -> dict[str, int]:
        result = await session.execute(
            text(
                "SELECT count(*) FROM source_record "
                "WHERE source_code = :source_code AND external_id = :external_id"
            ),
            {"source_code": source_code, "external_id": external_id},
        )
        return {"count": int(result.scalar_one())}

    return application


def _clients(
    *,
    apod: object | None = None,
    neows: object | None = None,
    donki: object | None = None,
    eonet: object | None = None,
    media: object | None = None,
) -> NASAClients:
    return NASAClients(
        apod=apod,  # type: ignore[arg-type]
        neows=neows,  # type: ignore[arg-type]
        donki=donki,  # type: ignore[arg-type]
        eonet=eonet,  # type: ignore[arg-type]
        media=media,  # type: ignore[arg-type]
    )


def test_postgres_readiness_and_request_session() -> None:
    application = _test_application()

    @application.get("/_integration/db-ping")
    async def database_ping(session: AsyncSession = Depends(get_db_session)) -> dict[str, int]:
        result = await session.execute(text("SELECT count(*) FROM data_source"))
        return {"sources": int(result.scalar_one())}

    with TestClient(application) as client:
        readiness = client.get("/health/ready")
        ping = client.get("/_integration/db-ping")

    assert readiness.status_code == 200
    assert readiness.json() == {"status": "ok", "database": "ready"}
    assert ping.status_code == 200
    assert ping.json()["sources"] >= 0


def test_postgres_apod_upsert_and_database_search_are_idempotent() -> None:
    application = _test_application()

    class FakeApodClient:
        async def get_by_date(self, _apod_date: date) -> ApodRecord:
            return ApodRecord(
                date=date(2026, 11, 13),
                post_id=123,
                title="A real galaxy fixture",
                media_type="image",
                explanation="Sanitized contract fixture.",
                permalink="https://science.nasa.gov/astronomy/apod/fixture/",
                url="https://images.nasa.gov/fixture.jpg",
                basic_html="<script>not returned</script>",
            )

    fake_clients = _clients(apod=FakeApodClient())
    application.dependency_overrides[get_nasa_clients] = lambda: fake_clients

    with TestClient(application) as client:
        first = client.get("/api/v1/astronomy/apod/2026-11-13")
        second = client.get("/api/v1/astronomy/apod/2026-11-13")
        search = client.get("/api/v1/astronomy/records", params={"q": "galaxy"})

    assert first.status_code == second.status_code == search.status_code == 200
    assert first.json()["provenance"]["source"] == "APOD"
    assert "basic_html" not in first.json()
    assert search.json()["total"] == 1
    assert len(search.json()["items"]) == 1


def test_postgres_neows_route_upserts_asteroid_and_approach() -> None:
    application = _test_application()

    class FakeNeoWsClient:
        async def feed(self, _start: date, _end: date) -> dict[str, Any]:
            return {"near_earth_objects": {"2026-11-14": [NEO_FIXTURE]}}

    NEO_FIXTURE = {
        "id": "54321",
        "name": "(54321) Test Asteroid",
        "absolute_magnitude_h": 20.2,
        "estimated_diameter": {
            "kilometers": {
                "estimated_diameter_min": 0.12,
                "estimated_diameter_max": 0.25,
            }
        },
        "is_potentially_hazardous_asteroid": True,
        "is_sentry_object": False,
        "nasa_jpl_url": "https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=54321",
        "close_approach_data": [
            {
                "close_approach_date": "2026-11-14",
                "epoch_date_close_approach": 1794614400000,
                "relative_velocity": {"kilometers_per_second": "12.5"},
                "miss_distance": {"kilometers": "1234567", "astronomical": "0.008"},
                "orbiting_body": "Earth",
            }
        ],
    }

    fake_clients = _clients(neows=FakeNeoWsClient())
    application.dependency_overrides[get_nasa_clients] = lambda: fake_clients
    params = {
        "close_approach_start": "2026-11-14",
        "close_approach_end": "2026-11-14",
        "minimum_diameter_km": "0.2",
        "maximum_diameter_km": "0.3",
    }

    with TestClient(application) as client:
        first = client.get("/api/v1/asteroids", params=params)
        second = client.get("/api/v1/asteroids", params=params)
        invalid_range = client.get(
            "/api/v1/asteroids",
            params={**params, "minimum_diameter_km": "1", "maximum_diameter_km": "0.5"},
        )
        count = client.get(
            "/_integration/source-count",
            params={"source_code": "NEOWS", "external_id": "54321"},
        )

    assert first.status_code == second.status_code == count.status_code == 200
    assert invalid_range.status_code == 422
    assert first.json()["total"] == 1
    assert first.json()["items"][0]["neo_id"] == "54321"
    assert first.json()["items"][0]["provenance"]["source"] == "NEOWS"
    assert len(first.json()["items"][0]["close_approaches"]) == 1
    assert count.json()["count"] == 1


def test_postgres_donki_route_preserves_provenance_and_upserts() -> None:
    application = _test_application()

    class FakeDONKIClient:
        async def events(self, _event_type: str, _start: date, _end: date) -> list[dict[str, Any]]:
            return [
                {
                    "activityID": "CME-2026-0001",
                    "type": "CME",
                    "startTime": "2026-11-13T11:30Z",
                    "note": "Fixture event summary.",
                    "link": "https://ccmc.gsfc.nasa.gov/DONKI/view/CME/fixture",
                }
            ]

    fake_clients = _clients(donki=FakeDONKIClient())
    application.dependency_overrides[get_nasa_clients] = lambda: fake_clients
    params = {"type": "CME", "start_date": "2026-11-13", "end_date": "2026-11-14"}

    with TestClient(application) as client:
        first = client.get("/api/v1/space-weather/events", params=params)
        second = client.get("/api/v1/space-weather/events", params=params)
        count = client.get(
            "/_integration/source-count",
            params={"source_code": "DONKI", "external_id": "CME:CME-2026-0001"},
        )

    assert first.status_code == second.status_code == count.status_code == 200
    event = first.json()["items"][0]
    assert event["provenance"]["source"] == "DONKI"
    assert event["event_id"] == "CME-2026-0001"
    assert event["source_url"].startswith("https://ccmc.gsfc.nasa.gov/")
    assert count.json()["count"] == 1


def test_postgres_eonet_route_saves_typed_event_and_provenance() -> None:
    application = _test_application()

    class FakeEONETClient:
        async def events(self, **_kwargs: Any) -> dict[str, Any]:
            return {
                "events": [
                    {
                        "id": "EONET_54321",
                        "title": "Fixture wildfire",
                        "description": "A bounded event fixture.",
                        "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_54321",
                        "categories": [{"id": "wildfires", "title": "Wildfires"}],
                        "sources": [
                            {"id": "FIRMS", "url": "https://firms.modaps.eosdis.nasa.gov/"}
                        ],
                        "geometry": [
                            {
                                "date": "2026-11-14T10:00:00Z",
                                "type": "Point",
                                "coordinates": [-120.5, 38.2],
                                "magnitudeValue": 4.5,
                                "magnitudeUnit": "km2",
                            }
                        ],
                    }
                ],
                "count": 1,
            }

    fake_clients = _clients(eonet=FakeEONETClient())
    application.dependency_overrides[get_nasa_clients] = lambda: fake_clients

    with TestClient(application) as client:
        first = client.get("/api/v1/earth-events", params={"status": "open"})
        second = client.get("/api/v1/earth-events", params={"status": "open"})
        count = client.get(
            "/_integration/source-count",
            params={"source_code": "EONET", "external_id": "EONET_54321"},
        )

    assert first.status_code == second.status_code == count.status_code == 200
    event = first.json()["items"][0]
    assert event["event_id"] == "EONET_54321"
    assert event["status"] == "open"
    assert event["provenance"]["source"] == "EONET"
    assert event["geometry"][0]["magnitudeValue"] == 4.5
    assert count.json()["count"] == 1


def test_postgres_media_route_upserts_rights_and_source_metadata() -> None:
    application = _test_application()

    class FakeMediaClient:
        search_calls = 0

        async def search(self, **_kwargs: Any) -> dict[str, Any]:
            self.search_calls += 1
            return {
                "collection": {
                    "items": [
                        {
                            "data": [
                                {
                                    "nasa_id": "PIA54321",
                                    "title": "Fixture image of Earth",
                                    "media_type": "image",
                                    "date_created": "2026-11-14T12:00:00Z",
                                    "description": "A media search contract fixture.",
                                    "photographer": "NASA Test Photographer",
                                    "copyright": "Public domain fixture notice.",
                                    "keywords": ["Earth", "test"],
                                }
                            ],
                            "links": [
                                {
                                    "rel": "preview",
                                    "href": "https://images.nasa.gov/preview/PIA54321.jpg",
                                }
                            ],
                        }
                    ],
                    "metadata": {"total_hits": 1},
                    "links": [],
                }
            }

    fake_clients = _clients(media=FakeMediaClient())
    application.dependency_overrides[get_nasa_clients] = lambda: fake_clients

    with TestClient(application) as client:
        first = client.get("/api/v1/media", params={"q": "Earth", "media_type": "image"})
        second = client.get("/api/v1/media", params={"q": "Earth", "media_type": "image"})
        detail = client.get("/api/v1/media/PIA54321")
        count = client.get(
            "/_integration/source-count",
            params={"source_code": "NASA_MEDIA", "external_id": "PIA54321"},
        )

    assert first.status_code == second.status_code == detail.status_code == count.status_code == 200
    item = first.json()["items"][0]
    assert item["nasa_id"] == "PIA54321"
    assert item["rights_note"] == "Public domain fixture notice."
    assert item["provenance"]["source"] == "NASA_MEDIA"
    assert item["thumbnail_url"] == "https://images.nasa.gov/preview/PIA54321.jpg"
    assert detail.json()["description"] == "A media search contract fixture."
    assert fake_clients.media.search_calls == 2  # The detail route serves its stored record.
    assert count.json()["count"] == 1
