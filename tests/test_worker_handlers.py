"""Mocked checks for bounded, explicitly allowlisted ingestion handlers."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.nasa_apod import NasaApodClient
from app.clients.nasa_donki import DONKIClient
from app.clients.nasa_eonet import EONETClient
from app.clients.nasa_media import NASAMediaClient
from app.clients.nasa_neows import NeoWsClient
from app.clients.registry import NASAClients
from app.models.apod import ApodRecord
from app.services import ingestion
from app.worker.handlers import (
    IngestionBatch,
    InvalidIngestionJob,
    fetch_ingestion_batch,
    persist_ingestion_batch,
)
from app.worker.jobs import ClaimedJob


def _job(
    source_code: str,
    job_type: str,
    *,
    window_start: date | None = date(2026, 11, 13),
    window_end: date | None = date(2026, 11, 13),
) -> ClaimedJob:
    return ClaimedJob(
        id=uuid4(),
        source_code=source_code,
        job_type=job_type,
        window_start=window_start,
        window_end=window_end,
        attempts=1,
        worker_id="worker-test",
    )


def _clients(
    *,
    apod: object | None = None,
    neows: object | None = None,
    donki: object | None = None,
    eonet: object | None = None,
) -> NASAClients:
    return NASAClients(
        apod=cast(NasaApodClient, apod or object()),
        neows=cast(NeoWsClient, neows or object()),
        donki=cast(DONKIClient, donki or object()),
        eonet=cast(EONETClient, eonet or object()),
        media=cast(NASAMediaClient, object()),
    )


def test_apod_handler_bounds_window_and_uses_fixed_page_limit() -> None:
    async def scenario() -> None:
        class FakeApod:
            async def search(self, **kwargs: Any) -> list[ApodRecord]:
                assert kwargs == {
                    "start_date": date(2026, 11, 1),
                    "end_date": date(2026, 11, 25),
                    "page": 1,
                    "page_size": 25,
                }
                return []

        clients = _clients(apod=FakeApod())
        bounded = _job(
            "APOD",
            "apod_window",
            window_start=date(2026, 11, 1),
            window_end=date(2026, 11, 25),
        )
        batch = await fetch_ingestion_batch(bounded, clients)
        assert batch.source_code == "APOD" and batch.records == []

        overlong = _job(
            "APOD",
            "apod_window",
            window_start=date(2026, 11, 1),
            window_end=date(2026, 11, 26),
        )
        with pytest.raises(InvalidIngestionJob):
            await fetch_ingestion_batch(overlong, clients)

    asyncio.run(scenario())


def test_neows_handler_deduplicates_objects_and_uses_short_window() -> None:
    async def scenario() -> None:
        class FakeNeoWs:
            async def feed(self, start_date: date, end_date: date) -> dict[str, Any]:
                assert start_date == date(2026, 11, 13)
                assert end_date == date(2026, 11, 20)
                return {
                    "near_earth_objects": {
                        "2026-11-13": [{"id": "1", "name": "one"}],
                        "2026-11-14": [{"id": "1", "name": "one-updated"}],
                    }
                }

        batch = await fetch_ingestion_batch(
            _job("NEOWS", "neows_feed", window_end=date(2026, 11, 20)), _clients(neows=FakeNeoWs())
        )
        assert batch.source_code == "NEOWS"
        assert batch.records == [{"id": "1", "name": "one-updated"}]

    asyncio.run(scenario())


def test_donki_handler_accepts_only_official_event_types() -> None:
    async def scenario() -> None:
        class FakeDONKI:
            async def events(
                self, event_type: str, start_date: date, end_date: date
            ) -> list[dict[str, Any]]:
                assert event_type == "CME"
                assert start_date == date(2026, 11, 13)
                assert end_date == date(2026, 11, 13)
                return [{"activityID": "fixture"}]

        clients = _clients(donki=FakeDONKI())
        batch = await fetch_ingestion_batch(_job("DONKI", "donki:CME"), clients)
        assert batch.source_code == "DONKI" and len(batch.records) == 1
        with pytest.raises(InvalidIngestionJob):
            await fetch_ingestion_batch(_job("DONKI", "donki:untrusted"), clients)

    asyncio.run(scenario())


def test_eonet_handler_requests_bounded_envelope_and_accepts_current_events() -> None:
    async def scenario() -> None:
        class FakeEONET:
            async def events(self, **kwargs: Any) -> dict[str, Any]:
                assert kwargs == {
                    "status": "all",
                    "start_date": None,
                    "end_date": None,
                    "limit": 1000,
                }
                return {"events": [{"id": "EONET_1"}]}

        batch = await fetch_ingestion_batch(
            _job("EONET", "eonet_events", window_start=None, window_end=None),
            _clients(eonet=FakeEONET()),
        )
        assert batch.source_code == "EONET" and batch.records == [{"id": "EONET_1"}]

    asyncio.run(scenario())


def test_persistence_dispatch_preserves_source_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        calls: list[tuple[str, object]] = []

        async def record_call(name: str, record: object) -> None:
            calls.append((name, record))

        async def fake_apod(_session: Any, record: object, _retrieved_at: datetime) -> None:
            await record_call("APOD", record)

        async def fake_neo(_session: Any, record: object, _retrieved_at: datetime) -> None:
            await record_call("NEOWS", record)

        async def fake_donki(
            _session: Any, event_type: str, record: object, _retrieved_at: datetime
        ) -> None:
            await record_call(f"DONKI:{event_type}", record)

        async def fake_eonet(_session: Any, record: object, _retrieved_at: datetime) -> None:
            await record_call("EONET", record)

        monkeypatch.setattr(ingestion, "persist_apod", fake_apod)
        monkeypatch.setattr(ingestion, "persist_neo", fake_neo)
        monkeypatch.setattr(ingestion, "persist_donki", fake_donki)
        monkeypatch.setattr(ingestion, "persist_eonet", fake_eonet)

        retrieved_at = datetime.now(UTC)
        apod_record = ApodRecord(date=date(2026, 11, 13), title="Fixture", media_type="image")
        batches = [
            (_job("APOD", "apod_window"), IngestionBatch("APOD", [apod_record], retrieved_at)),
            (_job("NEOWS", "neows_feed"), IngestionBatch("NEOWS", [{"id": "1"}], retrieved_at)),
            (
                _job("DONKI", "donki:CME"),
                IngestionBatch("DONKI", [{"activityID": "1"}], retrieved_at),
            ),
            (
                _job("EONET", "eonet_events"),
                IngestionBatch("EONET", [{"id": "EONET_1"}], retrieved_at),
            ),
        ]
        for job, batch in batches:
            counts = await persist_ingestion_batch(job, batch, cast(AsyncSession, object()))
            assert counts == {"received": 1, "persisted": 1}
        assert [name for name, _ in calls] == ["APOD", "NEOWS", "DONKI:CME", "EONET"]

    asyncio.run(scenario())
