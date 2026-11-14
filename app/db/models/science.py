"""Normalized NASA domain records stored alongside source provenance."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import JSON_DOCUMENT

if TYPE_CHECKING:
    from app.db.models.sources import SourceRecord


class APODRecord(Base):
    """Normalized APOD Basic item; HTML is not stored as renderable markup."""

    __tablename__ = "apod_record"
    __table_args__ = (
        CheckConstraint("media_type IN ('image', 'video', 'iframe')", name="media_type_allowed"),
        Index("ix_apod_record_date_desc", "apod_date"),
    )

    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_record.id", ondelete="CASCADE"), primary_key=True
    )
    apod_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    page_url: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[str | None] = mapped_column(Text)
    hd_url: Mapped[str | None] = mapped_column(Text)
    alt_text: Mapped[str | None] = mapped_column(Text)
    credit: Mapped[str | None] = mapped_column(Text)
    copyright: Mapped[str | None] = mapped_column(Text)

    source_record: Mapped["SourceRecord"] = relationship(back_populates="apod")


class NEOObject(Base):
    """Near-Earth object measurements and NASA classification flags."""

    __tablename__ = "neo_object"
    __table_args__ = (
        CheckConstraint(
            "diameter_min_km IS NULL OR diameter_max_km IS NULL "
            "OR diameter_min_km <= diameter_max_km",
            name="diameter_ordered",
        ),
        UniqueConstraint("neo_id", name="uq_neo_object_neo_id"),
        Index("ix_neo_object_name", "name"),
    )

    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_record.id", ondelete="CASCADE"), primary_key=True
    )
    neo_id: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    absolute_magnitude: Mapped[Decimal | None] = mapped_column(Numeric(12, 5))
    diameter_min_km: Mapped[Decimal | None] = mapped_column(Numeric(18, 9))
    diameter_max_km: Mapped[Decimal | None] = mapped_column(Numeric(18, 9))
    potentially_hazardous: Mapped[bool | None] = mapped_column()
    sentry_object: Mapped[bool | None] = mapped_column()
    jpl_url: Mapped[str | None] = mapped_column(Text)

    source_record: Mapped["SourceRecord"] = relationship(back_populates="neo_object")
    approaches: Mapped[list["NEOApproach"]] = relationship(back_populates="neo_object")


class NEOApproach(Base):
    """One asteroid close approach with the original NASA date and units."""

    __tablename__ = "neo_approach"
    __table_args__ = (
        UniqueConstraint(
            "neo_id", "approach_date", "orbiting_body", name="uq_neo_approach_identity"
        ),
        CheckConstraint("velocity_km_s IS NULL OR velocity_km_s >= 0", name="velocity_nonnegative"),
        CheckConstraint(
            "miss_distance_km IS NULL OR miss_distance_km >= 0", name="distance_nonnegative"
        ),
        Index("ix_neo_approach_date", "approach_date"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_record.id", ondelete="CASCADE"), nullable=False
    )
    neo_id: Mapped[str] = mapped_column(
        ForeignKey("neo_object.neo_id", ondelete="CASCADE"), nullable=False
    )
    approach_date: Mapped[date] = mapped_column(Date, nullable=False)
    epoch_date_close: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    velocity_km_s: Mapped[Decimal | None] = mapped_column(Numeric(20, 9))
    miss_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(30, 6))
    miss_distance_au: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    orbiting_body: Mapped[str | None] = mapped_column(String(80))

    source_record: Mapped["SourceRecord"] = relationship(back_populates="approaches")
    neo_object: Mapped[NEOObject] = relationship(back_populates="approaches")


class SpaceWeatherEvent(Base):
    """Type-specific DONKI event fields plus an extensible preserved detail map."""

    __tablename__ = "space_weather_event"
    __table_args__ = (Index("ix_space_weather_type_start", "event_type", "start_time"),)

    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_record.id", ondelete="CASCADE"), primary_key=True
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    activity_id: Mapped[str | None] = mapped_column(String(255))
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    class_type: Mapped[str | None] = mapped_column(String(80))
    source_location: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    link: Mapped[str | None] = mapped_column(Text)

    source_record: Mapped["SourceRecord"] = relationship(back_populates="space_weather_event")


class EarthEvent(Base):
    """EONET curated event with time-versioned geometry in JSON form."""

    __tablename__ = "earth_event"
    __table_args__ = (Index("ix_earth_event_closed_opened", "closed_at", "opened_at"),)

    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_record.id", ondelete="CASCADE"), primary_key=True
    )
    eonet_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    categories: Mapped[list[Any]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    sources: Mapped[list[Any]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    geometry: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON_DOCUMENT)
    geometry_type: Mapped[str | None] = mapped_column(String(40))
    magnitude_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    magnitude_unit: Mapped[str | None] = mapped_column(String(80))

    source_record: Mapped["SourceRecord"] = relationship(back_populates="earth_event")


class MediaRecord(Base):
    """NASA Media Library descriptive metadata and original asset-manifest links."""

    __tablename__ = "media_record"
    __table_args__ = (Index("ix_media_record_type_created", "media_type", "date_created"),)

    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_record.id", ondelete="CASCADE"), primary_key=True
    )
    nasa_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(String(24), nullable=False)
    date_created: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description: Mapped[str | None] = mapped_column(Text)
    description_508: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[Any]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    creators: Mapped[list[Any]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    asset_manifest_url: Mapped[str] = mapped_column(Text, nullable=False)
    detail_url: Mapped[str] = mapped_column(Text, nullable=False)
    rights_note: Mapped[str | None] = mapped_column(Text)

    source_record: Mapped["SourceRecord"] = relationship(back_populates="media_record")
