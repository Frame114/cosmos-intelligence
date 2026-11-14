"""PostgreSQL-backed ingestion job enqueueing, leases, retries, and completion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.jobs import IngestionJob

MAX_JOB_ATTEMPTS = 5
MAX_LEASE_SECONDS = 3600
MAX_RETRY_DELAY_SECONDS = 3600
_WORKER_ID = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")
_ERROR_CODE = re.compile(r"^[a-z0-9_]{1,80}$")
_SCHEDULE_KEY = re.compile(r"^[A-Za-z0-9:._-]{1,255}$")


@dataclass(frozen=True, slots=True)
class ClaimedJob:
    """The immutable fields needed by a handler after the claim transaction commits."""

    id: UUID
    source_code: str
    job_type: str
    window_start: date | None
    window_end: date | None
    attempts: int
    worker_id: str


async def enqueue_job(
    session: AsyncSession,
    *,
    source_code: str,
    job_type: str,
    window_start: date | None = None,
    window_end: date | None = None,
    next_run_at: datetime | None = None,
    schedule_key: str | None = None,
) -> UUID:
    """Add a validated bounded job to the caller's transaction."""

    if window_start and window_end and window_start > window_end:
        raise ValueError("Job window must be ordered.")
    normalized_type = job_type.strip()
    if not normalized_type or len(normalized_type) > 80:
        raise ValueError("Job type is invalid.")
    scheduled_at = next_run_at or datetime.now(UTC)
    if scheduled_at.tzinfo is None:
        raise ValueError("Job schedule must include a timezone.")

    if schedule_key is not None:
        if not _SCHEDULE_KEY.fullmatch(schedule_key):
            raise ValueError("Schedule key is invalid.")
        job_id = uuid4()
        result = await session.execute(
            pg_insert(IngestionJob)
            .values(
                id=job_id,
                source_code=source_code,
                job_type=normalized_type,
                schedule_key=schedule_key,
                window_start=window_start,
                window_end=window_end,
                state="queued",
                next_run_at=scheduled_at.astimezone(UTC),
            )
            .on_conflict_do_nothing(index_elements=[IngestionJob.schedule_key])
            .returning(IngestionJob.id)
        )
        persisted_id = result.scalar_one_or_none()
        if persisted_id is not None:
            return persisted_id
        existing_id = await session.scalar(
            select(IngestionJob.id).where(IngestionJob.schedule_key == schedule_key)
        )
        if existing_id is None:
            raise RuntimeError("The scheduled job was not persisted.")
        return existing_id

    job = IngestionJob(
        source_code=source_code,
        job_type=normalized_type,
        window_start=window_start,
        window_end=window_end,
        state="queued",
        next_run_at=scheduled_at.astimezone(UTC),
    )
    session.add(job)
    await session.flush()
    return job.id


async def claim_next_job(
    session: AsyncSession,
    *,
    worker_id: str,
    lease_seconds: int = 300,
    now: datetime | None = None,
) -> ClaimedJob | None:
    """Claim one due job with row-level skip-locked semantics."""

    if not _WORKER_ID.fullmatch(worker_id):
        raise ValueError("Worker ID is invalid.")
    if not 1 <= lease_seconds <= MAX_LEASE_SECONDS:
        raise ValueError("Lease duration is outside the supported range.")
    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        raise ValueError("Claim time must include a timezone.")
    current_time = current_time.astimezone(UTC)

    # A job whose final worker disappeared must stop retrying after the lease expires.
    await session.execute(
        update(IngestionJob)
        .where(
            IngestionJob.state == "running",
            IngestionJob.lease_until <= current_time,
            IngestionJob.attempts >= MAX_JOB_ATTEMPTS,
        )
        .values(
            state="failed",
            lease_until=None,
            locked_by=None,
            finished_at=current_time,
            safe_error_code="lease_expired",
        )
    )

    eligible = or_(
        and_(IngestionJob.state == "queued", IngestionJob.next_run_at <= current_time),
        and_(
            IngestionJob.state == "running",
            IngestionJob.lease_until <= current_time,
            IngestionJob.attempts < MAX_JOB_ATTEMPTS,
        ),
    )
    job = await session.scalar(
        select(IngestionJob)
        .where(eligible)
        .order_by(IngestionJob.next_run_at, IngestionJob.created_at, IngestionJob.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        return None

    job.state = "running"
    job.attempts += 1
    job.locked_by = worker_id
    job.lease_until = current_time + timedelta(seconds=lease_seconds)
    job.started_at = current_time
    job.finished_at = None
    job.safe_error_code = None
    await session.flush()
    return ClaimedJob(
        id=job.id,
        source_code=job.source_code,
        job_type=job.job_type,
        window_start=job.window_start,
        window_end=job.window_end,
        attempts=job.attempts,
        worker_id=worker_id,
    )


async def renew_job_lease(
    session: AsyncSession,
    *,
    job_id: UUID,
    worker_id: str,
    lease_seconds: int = 300,
    now: datetime | None = None,
) -> bool:
    """Extend a live lease only for its current owner."""

    if not _WORKER_ID.fullmatch(worker_id):
        raise ValueError("Worker ID is invalid.")
    if not 1 <= lease_seconds <= MAX_LEASE_SECONDS:
        raise ValueError("Lease duration is outside the supported range.")
    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        raise ValueError("Heartbeat time must include a timezone.")
    current_time = current_time.astimezone(UTC)
    result = await session.execute(
        update(IngestionJob)
        .where(
            IngestionJob.id == job_id,
            IngestionJob.state == "running",
            IngestionJob.locked_by == worker_id,
            IngestionJob.lease_until > current_time,
        )
        .values(lease_until=current_time + timedelta(seconds=lease_seconds))
        .returning(IngestionJob.id)
    )
    return result.scalar_one_or_none() is not None


async def complete_job(
    session: AsyncSession,
    *,
    job_id: UUID,
    worker_id: str,
    counts: dict[str, int],
    now: datetime | None = None,
) -> bool:
    """Mark a job successful while its lease is current and still owned."""

    _validate_counts(counts)
    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        raise ValueError("Completion time must include a timezone.")
    current_time = current_time.astimezone(UTC)
    result = await session.execute(
        update(IngestionJob)
        .where(
            IngestionJob.id == job_id,
            IngestionJob.state == "running",
            IngestionJob.locked_by == worker_id,
            IngestionJob.lease_until > current_time,
        )
        .values(
            state="succeeded",
            counts=counts,
            lease_until=None,
            locked_by=None,
            finished_at=current_time,
            safe_error_code=None,
        )
        .returning(IngestionJob.id)
    )
    return result.scalar_one_or_none() is not None


async def fail_job(
    session: AsyncSession,
    *,
    job_id: UUID,
    worker_id: str,
    safe_error_code: str,
    retryable: bool,
    retry_delay_seconds: int = 30,
    now: datetime | None = None,
) -> bool:
    """Schedule a bounded retry or finish a job with a sanitized error code."""

    if not _WORKER_ID.fullmatch(worker_id):
        raise ValueError("Worker ID is invalid.")
    if not _ERROR_CODE.fullmatch(safe_error_code):
        raise ValueError("Safe error code is invalid.")
    if not 1 <= retry_delay_seconds <= MAX_RETRY_DELAY_SECONDS:
        raise ValueError("Retry delay is outside the supported range.")
    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        raise ValueError("Failure time must include a timezone.")
    current_time = current_time.astimezone(UTC)

    job = await session.scalar(
        select(IngestionJob)
        .where(
            IngestionJob.id == job_id,
            IngestionJob.state == "running",
            IngestionJob.locked_by == worker_id,
            IngestionJob.lease_until > current_time,
        )
        .with_for_update()
    )
    if job is None:
        return False

    should_retry = retryable and job.attempts < MAX_JOB_ATTEMPTS
    job.state = "queued" if should_retry else "failed"
    job.next_run_at = (
        current_time + timedelta(seconds=retry_delay_seconds) if should_retry else job.next_run_at
    )
    job.lease_until = None
    job.locked_by = None
    job.finished_at = None if should_retry else current_time
    job.safe_error_code = safe_error_code
    await session.flush()
    return True


def _validate_counts(counts: dict[str, int]) -> None:
    if len(counts) > 32:
        raise ValueError("Job result contains too many counters.")
    for name, value in counts.items():
        if not _ERROR_CODE.fullmatch(name):
            raise ValueError("Job counter name is invalid.")
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("Job counters must be nonnegative integers.")


def safe_job_counts(value: Any) -> dict[str, int]:
    """Normalize handler counters before persistence; omit unknown/untrusted values."""

    if not isinstance(value, dict):
        return {}
    return {
        key: count
        for key, count in value.items()
        if isinstance(key, str)
        and _ERROR_CODE.fullmatch(key)
        and isinstance(count, int)
        and not isinstance(count, bool)
        and count >= 0
    }
