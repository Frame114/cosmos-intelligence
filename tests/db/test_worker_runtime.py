"""PostgreSQL integration checks for allowlisted worker dispatch and persistence."""

from __future__ import annotations

import asyncio
import os
from datetime import date
from typing import cast

import pytest
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.clients.nasa_apod import NasaApodClient
from app.clients.nasa_donki import DONKIClient
from app.clients.nasa_eonet import EONETClient
from app.clients.nasa_media import NASAMediaClient
from app.clients.nasa_neows import NeoWsClient
from app.clients.registry import NASAClients
from app.db.models import APODRecord, DataSource, IngestionJob
from app.db.session import create_engine, get_sessionmaker
from app.models.apod import ApodRecord as APODResponse
from app.worker.jobs import enqueue_job
from app.worker.runtime import IngestionWorker

TEST_DATABASE_URL = os.environ.get("COSMOS_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="No disposable PostgreSQL URL configured."
)


def test_worker_persists_allowlisted_apod_job_and_rejects_unknown_type() -> None:
    async def scenario() -> None:
        engine = create_engine(TEST_DATABASE_URL)
        factory = get_sessionmaker(engine)

        class FakeApodClient:
            calls = 0

            async def search(
                self,
                *,
                start_date: date | None = None,
                end_date: date | None = None,
                page: int = 1,
                page_size: int = 20,
            ) -> list[APODResponse]:
                self.calls += 1
                assert start_date == date(2026, 11, 13)
                assert end_date == date(2026, 11, 13)
                assert page == 1 and page_size == 25
                return [
                    APODResponse(
                        date=date(2026, 11, 13),
                        title="Worker fixture",
                        media_type="image",
                        explanation="Sanitized worker integration fixture.",
                        permalink="https://science.nasa.gov/astronomy/apod/worker-fixture/",
                        url="https://images.nasa.gov/worker-fixture.jpg",
                    )
                ]

        apod = FakeApodClient()
        clients = NASAClients(
            apod=cast(NasaApodClient, apod),
            neows=cast(NeoWsClient, object()),
            donki=cast(DONKIClient, object()),
            eonet=cast(EONETClient, object()),
            media=cast(NASAMediaClient, object()),
        )

        try:
            async with factory.begin() as session:
                await session.execute(
                    pg_insert(DataSource)
                    .values(
                        code="APOD",
                        display_name="Astronomy Picture of the Day",
                        base_host="science.nasa.gov",
                        enabled=True,
                        policy={},
                    )
                    .on_conflict_do_nothing(index_elements=[DataSource.code])
                )
                valid_job_id = await enqueue_job(
                    session,
                    source_code="APOD",
                    job_type="apod_window",
                    window_start=date(2026, 11, 13),
                    window_end=date(2026, 11, 13),
                )
                invalid_job_id = await enqueue_job(
                    session,
                    source_code="APOD",
                    job_type="unlisted_operation",
                )

            worker = IngestionWorker(
                session_factory=factory,
                clients=clients,
                worker_id="worker-runtime-test",
                poll_interval_seconds=1,
                lease_seconds=30,
            )
            assert await worker.run_once()
            assert await worker.run_once()
            assert apod.calls == 1

            async with factory() as session:
                succeeded = await session.get(IngestionJob, valid_job_id)
                rejected = await session.get(IngestionJob, invalid_job_id)
                apod_record = await session.scalar(
                    select(APODRecord).where(APODRecord.apod_date == date(2026, 11, 13))
                )
                assert succeeded is not None and succeeded.state == "succeeded"
                assert succeeded.counts == {"received": 1, "persisted": 1}
                assert rejected is not None and rejected.state == "failed"
                assert rejected.safe_error_code == "job_invalid"
                assert apod_record is not None and apod_record.title == "Worker fixture"
        finally:
            await engine.dispose()

    asyncio.run(scenario())
