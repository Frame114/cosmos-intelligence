"""Upstream source registry and immutable-identity source records."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import JSON_DOCUMENT

if TYPE_CHECKING:
    from app.db.models.jobs import IngestionJob
    from app.db.models.science import (
        APODRecord,
        EarthEvent,
        MediaRecord,
        NEOApproach,
        NEOObject,
        SpaceWeatherEvent,
    )


class DataSource(Base):
    """Allowlisted NASA service with safe host metadata and policy settings."""

    __tablename__ = "data_source"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    base_host: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    policy: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    records: Mapped[list["SourceRecord"]] = relationship(back_populates="source")
    jobs: Mapped[list["IngestionJob"]] = relationship(back_populates="source")


class SourceRecord(Base):
    """Raw, provenance-bearing record keyed by source and external identifier."""

    __tablename__ = "source_record"
    __table_args__ = (
        UniqueConstraint("source_code", "external_id", name="uq_source_record_identity"),
        Index("ix_source_record_source_retrieved", "source_code", "retrieved_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_code: Mapped[str] = mapped_column(
        ForeignKey("data_source.code", ondelete="RESTRICT"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    normalizer_version: Mapped[str] = mapped_column(String(80), nullable=False, default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    source: Mapped[DataSource] = relationship(back_populates="records")
    apod: Mapped["APODRecord | None"] = relationship(
        back_populates="source_record", cascade="all, delete-orphan", uselist=False
    )
    neo_object: Mapped["NEOObject | None"] = relationship(
        back_populates="source_record", cascade="all, delete-orphan", uselist=False
    )
    approaches: Mapped[list["NEOApproach"]] = relationship(
        back_populates="source_record", cascade="all, delete-orphan"
    )
    space_weather_event: Mapped["SpaceWeatherEvent | None"] = relationship(
        back_populates="source_record", cascade="all, delete-orphan", uselist=False
    )
    earth_event: Mapped["EarthEvent | None"] = relationship(
        back_populates="source_record", cascade="all, delete-orphan", uselist=False
    )
    media_record: Mapped["MediaRecord | None"] = relationship(
        back_populates="source_record", cascade="all, delete-orphan", uselist=False
    )
