"""PostgreSQL tests for durable ingestion job leases and retry scheduling."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import DataSource
from app.db.models.jobs import IngestionJob
from app.db.session import create_engine, get_sessionmaker
from app.worker.jobs import claim_next_job, complete_job, enqueue_job, fail_job, renew_job_lease

TEST_DATABASE_URL = os.environ.get("COSMOS_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="No disposable PostgreSQL URL configured."
)


async def _seed_neows_source(factory: async_sessionmaker[AsyncSession]) -> None:
    async with factory.begin() as session:
        await session.execute(
            pg_insert(DataSource)
            .values(
                code="NEOWS",
                display_name="Near-Earth Object Web Service",
                base_host="api.nasa.gov",
                enabled=True,
                policy={},
            )
            .on_conflict_do_nothing(index_elements=[DataSource.code])
        )


def test_postgres_job_claim_is_exclusive_and_expired_lease_is_recoverable() -> None:
    async def scenario() -> None:
        engine = create_engine(TEST_DATABASE_URL)
        factory = get_sessionmaker(engine)
        try:
            await _seed_neows_source(factory)
            scheduled_at = datetime(2026, 11, 14, 12, tzinfo=UTC)
            async with factory.begin() as session:
                job_id = await enqueue_job(
                    session,
                    source_code="NEOWS",
                    job_type="neows_window",
                    window_start=date(2026, 11, 14),
                    window_end=date(2026, 11, 20),
                    next_run_at=scheduled_at,
                )

            async def claim(worker_id: str):
                async with factory.begin() as session:
                    result = await claim_next_job(
                        session,
                        worker_id=worker_id,
                        lease_seconds=300,
                        now=scheduled_at,
                    )
                    if result is not None:
                        await asyncio.sleep(0.05)
                    return result

            claims = await asyncio.gather(claim("worker-a"), claim("worker-b"))
            successful_claims = [item for item in claims if item is not None]
            assert len(successful_claims) == 1
            first_claim = successful_claims[0]
            assert first_claim.id == job_id
            assert first_claim.attempts == 1

            async with factory.begin() as session:
                assert not await renew_job_lease(
                    session,
                    job_id=job_id,
                    worker_id="wrong-owner",
                    now=scheduled_at + timedelta(seconds=1),
                )
                assert await renew_job_lease(
                    session,
                    job_id=job_id,
                    worker_id=first_claim.worker_id,
                    lease_seconds=300,
                    now=scheduled_at + timedelta(seconds=1),
                )

            reclaimed_at = scheduled_at + timedelta(seconds=302)
            async with factory.begin() as session:
                recovered = await claim_next_job(
                    session,
                    worker_id="worker-recovery",
                    lease_seconds=300,
                    now=reclaimed_at,
                )
            assert recovered is not None
            assert recovered.id == job_id
            assert recovered.attempts == 2
            assert recovered.worker_id == "worker-recovery"

            async with factory.begin() as session:
                assert not await complete_job(
                    session,
                    job_id=job_id,
                    worker_id=first_claim.worker_id,
                    counts={"received": 1},
                    now=reclaimed_at,
                )
                assert await complete_job(
                    session,
                    job_id=job_id,
                    worker_id=recovered.worker_id,
                    counts={"received": 4, "inserted": 2, "updated": 1, "unchanged": 1},
                    now=reclaimed_at + timedelta(seconds=1),
                )

            async with factory.begin() as session:
                state = await session.scalar(
                    select(IngestionJob.state).where(IngestionJob.id == job_id)
                )
                assert state == "succeeded"
        finally:
            await engine.dispose()

    asyncio.run(scenario())


def test_postgres_job_retry_waits_until_due_and_stops_at_attempt_limit() -> None:
    async def scenario() -> None:
        engine = create_engine(TEST_DATABASE_URL)
        factory = get_sessionmaker(engine)
        try:
            await _seed_neows_source(factory)
            scheduled_at = datetime(2026, 11, 14, 13, tzinfo=UTC)
            async with factory.begin() as session:
                job_id = await enqueue_job(
                    session,
                    source_code="NEOWS",
                    job_type="neows_window",
                    window_start=date(2026, 11, 14),
                    window_end=date(2026, 11, 20),
                    next_run_at=scheduled_at,
                )

            async with factory.begin() as session:
                claimed = await claim_next_job(
                    session,
                    worker_id="worker-retry",
                    now=scheduled_at,
                )
            assert claimed is not None and claimed.attempts == 1

            async with factory.begin() as session:
                assert not await fail_job(
                    session,
                    job_id=job_id,
                    worker_id="wrong-owner",
                    safe_error_code="upstream_timeout",
                    retryable=True,
                    now=scheduled_at + timedelta(seconds=1),
                )
                assert await fail_job(
                    session,
                    job_id=job_id,
                    worker_id=claimed.worker_id,
                    safe_error_code="upstream_timeout",
                    retryable=True,
                    retry_delay_seconds=30,
                    now=scheduled_at + timedelta(seconds=1),
                )

            async with factory.begin() as session:
                too_early = await claim_next_job(
                    session,
                    worker_id="worker-retry",
                    now=scheduled_at + timedelta(seconds=29),
                )
            assert too_early is None

            current_attempt = 1
            claim_time = scheduled_at + timedelta(seconds=32)
            while current_attempt < 5:
                async with factory.begin() as session:
                    claimed = await claim_next_job(
                        session,
                        worker_id="worker-retry",
                        now=claim_time,
                    )
                assert claimed is not None
                current_attempt = claimed.attempts
                async with factory.begin() as session:
                    assert await fail_job(
                        session,
                        job_id=job_id,
                        worker_id=claimed.worker_id,
                        safe_error_code="upstream_timeout",
                        retryable=True,
                        retry_delay_seconds=30,
                        now=claim_time + timedelta(seconds=1),
                    )
                claim_time += timedelta(seconds=32)

            async with factory.begin() as session:
                state = await session.scalar(
                    select(IngestionJob.state).where(IngestionJob.id == job_id)
                )
                assert state == "failed"
                assert not await claim_next_job(
                    session,
                    worker_id="worker-retry",
                    now=claim_time + timedelta(days=1),
                )
        finally:
            await engine.dispose()

    asyncio.run(scenario())
