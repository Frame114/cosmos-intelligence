"""Deterministic daily windows for bounded source ingestion."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import DataSource
from app.services.ingestion import SOURCE_INFO
from app.worker.jobs import enqueue_job

DAILY_JOB_WINDOWS: tuple[tuple[str, str, int], ...] = (
    ("APOD", "apod_window", 2),
    ("NEOWS", "neows_feed", 6),
    ("DONKI", "donki:notifications", 6),
    ("EONET", "eonet_events", 29),
)


async def enqueue_daily_jobs(
    session: AsyncSession,
    *,
    as_of: date | None = None,
) -> dict[str, UUID]:
    """Idempotently enqueue four bounded daily source windows for the supplied UTC date."""

    scheduled_date = as_of or datetime.now(UTC).date()
    for source_code, _job_type, _lookback_days in DAILY_JOB_WINDOWS:
        display_name, base_host = SOURCE_INFO[source_code]
        await session.execute(
            pg_insert(DataSource)
            .values(
                code=source_code,
                display_name=display_name,
                base_host=base_host,
                enabled=True,
                policy={},
            )
            .on_conflict_do_nothing(index_elements=[DataSource.code])
        )

    scheduled: dict[str, UUID] = {}
    for source_code, job_type, lookback_days in DAILY_JOB_WINDOWS:
        window_start = scheduled_date - timedelta(days=lookback_days)
        schedule_key = (
            f"daily:{source_code}:{job_type}:"
            f"{window_start.isoformat()}:{scheduled_date.isoformat()}"
        )
        scheduled[schedule_key] = await enqueue_job(
            session,
            source_code=source_code,
            job_type=job_type,
            window_start=window_start,
            window_end=scheduled_date,
            next_run_at=datetime.now(UTC),
            schedule_key=schedule_key,
        )
    return scheduled


async def enqueue_daily_jobs_transactionally(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    as_of: date | None = None,
) -> dict[str, UUID]:
    """Run the daily scheduler inside one short PostgreSQL transaction."""

    async with session_factory.begin() as session:
        return await enqueue_daily_jobs(session, as_of=as_of)
