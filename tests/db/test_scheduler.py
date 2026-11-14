"""PostgreSQL checks for deterministic, repeat-safe daily job schedules."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import func, select, update

from app.db.models import IngestionJob
from app.db.session import create_engine, get_sessionmaker
from app.worker.scheduler import DAILY_JOB_WINDOWS, enqueue_daily_jobs_transactionally

TEST_DATABASE_URL = os.environ.get("COSMOS_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="No disposable PostgreSQL URL configured."
)


def test_daily_schedule_is_bounded_and_idempotent_per_utc_day() -> None:
    async def scenario() -> None:
        engine = create_engine(TEST_DATABASE_URL)
        factory = get_sessionmaker(engine)
        as_of = date(2026, 11, 14)
        try:
            first = await enqueue_daily_jobs_transactionally(factory, as_of=as_of)
            repeated = await enqueue_daily_jobs_transactionally(factory, as_of=as_of)
            following_day = await enqueue_daily_jobs_transactionally(
                factory, as_of=date(2026, 11, 15)
            )

            assert len(first) == len(DAILY_JOB_WINDOWS) == 4
            assert repeated == first
            assert len(following_day) == 4
            assert set(first.values()).isdisjoint(following_day.values())

            async with factory.begin() as session:
                job_count = await session.scalar(
                    select(func.count(IngestionJob.id)).where(
                        IngestionJob.schedule_key.is_not(None)
                    )
                )
                assert job_count == 8
                for job_id in first.values():
                    job = await session.get(IngestionJob, job_id)
                    assert job is not None
                    assert job.window_start is not None and job.window_end == as_of
                    assert 0 <= (job.window_end - job.window_start).days <= 29
                await session.execute(
                    update(IngestionJob)
                    .where(IngestionJob.id.in_([*first.values(), *following_day.values()]))
                    .values(state="succeeded", finished_at=datetime.now(UTC))
                )
        finally:
            await engine.dispose()

    asyncio.run(scenario())
