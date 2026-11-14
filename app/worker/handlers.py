"""Allowlisted, bounded handlers for durable NASA ingestion jobs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.nasa_donki import DONKI_EVENT_TYPES
from app.clients.registry import NASAClients
from app.core.errors import UpstreamError
from app.models.apod import ApodRecord
from app.worker.jobs import ClaimedJob

MAX_APOD_WINDOW_DAYS = 25
MAX_EONET_WINDOW_DAYS = 3650


class InvalidIngestionJob(ValueError):
    """A queued job is not a supported or safely bounded NASA operation."""


@dataclass(frozen=True, slots=True)
class IngestionBatch:
    """Fetched, bounded records ready for one idempotent persistence transaction."""

    source_code: str
    records: Sequence[ApodRecord | dict[str, Any]]
    retrieved_at: datetime


def _require_window(
    job: ClaimedJob,
    *,
    max_span_days: int,
    allow_missing: bool = False,
) -> tuple[date, date] | None:
    if job.window_start is None or job.window_end is None:
        if allow_missing and job.window_start is None and job.window_end is None:
            return None
        raise InvalidIngestionJob("The job requires both window boundaries.")
    if job.window_start > job.window_end:
        raise InvalidIngestionJob("The job window is inverted.")
    if (job.window_end - job.window_start).days >= max_span_days:
        raise InvalidIngestionJob("The job window exceeds its source limit.")
    return job.window_start, job.window_end


async def fetch_ingestion_batch(job: ClaimedJob, clients: NASAClients) -> IngestionBatch:
    """Fetch only an explicitly supported source/job pair and bounded window."""

    if (job.source_code, job.job_type) == ("APOD", "apod_window"):
        window = _require_window(job, max_span_days=MAX_APOD_WINDOW_DAYS)
        assert window is not None
        apod_records = await clients.apod.search(
            start_date=window[0], end_date=window[1], page=1, page_size=MAX_APOD_WINDOW_DAYS
        )
        return IngestionBatch("APOD", apod_records, datetime.now(UTC))

    if (job.source_code, job.job_type) == ("NEOWS", "neows_feed"):
        window = _require_window(job, max_span_days=8)
        assert window is not None
        payload = await clients.neows.feed(window[0], window[1])
        objects_by_id: dict[str, dict[str, Any]] = {}
        for records in payload["near_earth_objects"].values():
            if not isinstance(records, list):
                continue
            for record in records:
                if isinstance(record, dict) and isinstance(record.get("id"), str):
                    objects_by_id[record["id"]] = record
        return IngestionBatch("NEOWS", list(objects_by_id.values()), datetime.now(UTC))

    if job.source_code == "DONKI" and job.job_type.startswith("donki:"):
        event_type = job.job_type.removeprefix("donki:")
        if event_type not in DONKI_EVENT_TYPES:
            raise InvalidIngestionJob("The DONKI event type is not allowlisted.")
        window = _require_window(job, max_span_days=31)
        assert window is not None
        donki_records = await clients.donki.events(event_type, window[0], window[1])
        return IngestionBatch("DONKI", donki_records, datetime.now(UTC))

    if (job.source_code, job.job_type) == ("EONET", "eonet_events"):
        window = _require_window(job, max_span_days=MAX_EONET_WINDOW_DAYS, allow_missing=True)
        payload = await clients.eonet.events(
            status="all",
            start_date=window[0] if window else None,
            end_date=window[1] if window else None,
            limit=1000,
        )
        raw_events = payload.get("events")
        if not isinstance(raw_events, list) or not all(
            isinstance(item, dict) for item in raw_events
        ):
            raise UpstreamError(
                "EONET",
                "upstream_schema_error",
                "EONET returned an unexpected events list.",
                retryable=False,
            )
        return IngestionBatch("EONET", raw_events, datetime.now(UTC))

    raise InvalidIngestionJob("The source and job type combination is not allowlisted.")


async def persist_ingestion_batch(
    job: ClaimedJob,
    batch: IngestionBatch,
    session: AsyncSession,
) -> dict[str, int]:
    """Persist a validated batch while preserving each provider's source identity."""

    from app.services.ingestion import (
        persist_apod,
        persist_donki,
        persist_eonet,
        persist_neo,
    )

    if job.source_code != batch.source_code:
        raise InvalidIngestionJob("The fetched source does not match the claimed job.")

    for record in batch.records:
        if batch.source_code == "APOD" and isinstance(record, ApodRecord):
            await persist_apod(session, record, batch.retrieved_at)
        elif batch.source_code == "NEOWS" and isinstance(record, dict):
            await persist_neo(session, record, batch.retrieved_at)
        elif batch.source_code == "DONKI" and isinstance(record, dict):
            event_type = job.job_type.removeprefix("donki:")
            await persist_donki(session, event_type, record, batch.retrieved_at)
        elif batch.source_code == "EONET" and isinstance(record, dict):
            await persist_eonet(session, record, batch.retrieved_at)
        else:
            raise UpstreamError(
                batch.source_code,
                "upstream_schema_error",
                "The ingestion handler returned an unexpected record type.",
                retryable=False,
            )

    count = len(batch.records)
    return {"received": count, "persisted": count}
