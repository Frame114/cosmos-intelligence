"""Lease-aware worker loop for allowlisted NASA ingestion jobs."""

from __future__ import annotations

import asyncio
import logging
from time import monotonic
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.clients.registry import NASAClients
from app.core.errors import UpstreamError
from app.worker.handlers import (
    InvalidIngestionJob,
    fetch_ingestion_batch,
    persist_ingestion_batch,
)
from app.worker.jobs import (
    ClaimedJob,
    claim_next_job,
    complete_job,
    fail_job,
    renew_job_lease,
)
from app.worker.scheduler import enqueue_daily_jobs_transactionally

logger = logging.getLogger("cosmos.worker")


class IngestionWorker:
    """Claim, execute, heartbeat, and complete one durable job at a time."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        clients: NASAClients,
        worker_id: str | None = None,
        poll_interval_seconds: float = 2.0,
        lease_seconds: int = 300,
        schedules_enabled: bool = False,
    ) -> None:
        if not 0.25 <= poll_interval_seconds <= 60:
            raise ValueError("Poll interval is outside the supported range.")
        if not 30 <= lease_seconds <= 3600:
            raise ValueError("Lease duration is outside the supported range.")
        self.session_factory = session_factory
        self.clients = clients
        self.worker_id = worker_id or f"cosmos-worker-{uuid4().hex[:12]}"
        self.poll_interval_seconds = poll_interval_seconds
        self.lease_seconds = lease_seconds
        self.schedules_enabled = schedules_enabled

    async def run(self, stop_event: asyncio.Event) -> None:
        """Poll until a shutdown signal arrives; idle workers wait without spinning."""

        next_schedule_at = 0.0
        schedule_interval_seconds = 300.0
        while not stop_event.is_set():
            if self.schedules_enabled and monotonic() >= next_schedule_at:
                try:
                    await enqueue_daily_jobs_transactionally(self.session_factory)
                except Exception as error:
                    logger.error("Daily scheduling failed error_type=%s", type(error).__name__)
                    next_schedule_at = monotonic() + 60
                else:
                    next_schedule_at = monotonic() + schedule_interval_seconds
            did_work = await self.run_once()
            if not did_work:
                wait_seconds = self.poll_interval_seconds
                if self.schedules_enabled:
                    wait_seconds = min(wait_seconds, max(0.0, next_schedule_at - monotonic()))
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=wait_seconds)
                except TimeoutError:
                    pass

    async def run_once(self) -> bool:
        """Claim and process one due job. Return false when the queue is currently empty."""

        async with self.session_factory.begin() as session:
            job = await claim_next_job(
                session,
                worker_id=self.worker_id,
                lease_seconds=self.lease_seconds,
            )
        if job is None:
            return False

        done = asyncio.Event()
        lease_lost = asyncio.Event()
        heartbeat = asyncio.create_task(self._heartbeat(job, done, lease_lost))
        try:
            batch = await fetch_ingestion_batch(job, self.clients)
            if lease_lost.is_set():
                return True
            async with self.session_factory.begin() as session:
                counts = await persist_ingestion_batch(job, batch, session)
                if lease_lost.is_set():
                    raise _LeaseLost
            if lease_lost.is_set():
                return True
            async with self.session_factory.begin() as session:
                completed = await complete_job(
                    session,
                    job_id=job.id,
                    worker_id=self.worker_id,
                    counts=counts,
                )
            if completed:
                logger.info(
                    "Completed ingestion job id=%s source=%s records=%d",
                    job.id,
                    job.source_code,
                    counts["persisted"],
                )
            else:
                lease_lost.set()
                logger.warning("Ingestion job lease no longer owned id=%s", job.id)
        except _LeaseLost:
            logger.warning("Ingestion job lease lost before persistence committed id=%s", job.id)
        except InvalidIngestionJob:
            await self._fail(job, "job_invalid", retryable=False)
        except UpstreamError as error:
            await self._fail(job, error.code, retryable=error.retryable)
            logger.warning(
                "Ingestion job failed id=%s source=%s error_code=%s retryable=%s",
                job.id,
                job.source_code,
                error.code,
                error.retryable,
            )
        except Exception as error:
            await self._fail(job, "worker_error", retryable=True)
            logger.error(
                "Ingestion job failed id=%s source=%s error_type=%s",
                job.id,
                job.source_code,
                type(error).__name__,
            )
        finally:
            done.set()
            await heartbeat
        return True

    async def _heartbeat(
        self,
        job: ClaimedJob,
        done: asyncio.Event,
        lease_lost: asyncio.Event,
    ) -> None:
        interval = max(1.0, self.lease_seconds / 3)
        while not done.is_set():
            try:
                await asyncio.wait_for(done.wait(), timeout=interval)
                return
            except TimeoutError:
                pass
            try:
                async with self.session_factory.begin() as session:
                    renewed = await renew_job_lease(
                        session,
                        job_id=job.id,
                        worker_id=self.worker_id,
                        lease_seconds=self.lease_seconds,
                    )
            except Exception as error:
                lease_lost.set()
                logger.error(
                    "Ingestion job heartbeat failed id=%s error_type=%s",
                    job.id,
                    type(error).__name__,
                )
                return
            if not renewed:
                lease_lost.set()
                logger.warning("Ingestion job lease expired or changed owner id=%s", job.id)
                return

    async def _fail(self, job: ClaimedJob, code: str, *, retryable: bool) -> None:
        retry_delay_seconds = min(3600, 30 * (2 ** min(job.attempts - 1, 7)))
        async with self.session_factory.begin() as session:
            failed = await fail_job(
                session,
                job_id=job.id,
                worker_id=self.worker_id,
                safe_error_code=code,
                retryable=retryable,
                retry_delay_seconds=retry_delay_seconds,
            )
        if not failed:
            logger.warning("Could not update ingestion job after lease loss id=%s", job.id)


class _LeaseLost(Exception):
    """Abort the current record transaction if the worker no longer owns its lease."""


def create_worker_id() -> str:
    """Create a random safe worker identifier for process logs and leases."""

    return f"cosmos-worker-{uuid4().hex[:12]}"
