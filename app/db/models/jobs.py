"""Durable ingestion job state and sanitized upstream request telemetry."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import JSON_DOCUMENT

if TYPE_CHECKING:
    from app.db.models.sources import DataSource


class IngestionJob(Base):
    """Retryable, lease-protected request to ingest a bounded source window."""

    __tablename__ = "ingestion_job"
    __table_args__ = (
        CheckConstraint(
            "state IN ('queued', 'running', 'succeeded', 'failed')", name="state_allowed"
        ),
        CheckConstraint("attempts >= 0", name="attempts_nonnegative"),
        Index("ix_ingestion_job_due", "state", "next_run_at"),
        Index("uq_ingestion_job_schedule_key", "schedule_key", unique=True),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_code: Mapped[str] = mapped_column(
        ForeignKey("data_source.code", ondelete="RESTRICT"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    schedule_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    window_start: Mapped[date | None] = mapped_column(Date)
    window_end: Mapped[date | None] = mapped_column(Date)
    state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued", server_default="queued"
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    next_run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(120))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    counts: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=dict, server_default="{}"
    )
    safe_error_code: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    source: Mapped["DataSource"] = relationship(back_populates="jobs")


class APIRequestLog(Base):
    """Bounded metadata about upstream calls; never stores URL queries or payloads."""

    __tablename__ = "api_request_log"
    __table_args__ = (
        Index("ix_api_request_log_started", "started_at"),
        Index("ix_api_request_log_source_started", "source_code", "started_at"),
        CheckConstraint("duration_ms >= 0", name="duration_nonnegative"),
        CheckConstraint("retry_count >= 0", name="retry_count_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_code: Mapped[str | None] = mapped_column(
        ForeignKey("data_source.code", ondelete="SET NULL")
    )
    operation: Mapped[str] = mapped_column(String(120), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status_code: Mapped[int | None] = mapped_column(SmallInteger)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer)
    request_id: Mapped[str | None] = mapped_column(String(128))
    safe_error_code: Mapped[str | None] = mapped_column(String(80))
