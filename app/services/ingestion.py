"""Idempotent source-provenance persistence for validated NASA records."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UpstreamError
from app.db.models import (
    APODRecord,
    DataSource,
    EarthEvent,
    MediaRecord,
    NEOApproach,
    NEOObject,
    SourceRecord,
    SpaceWeatherEvent,
)
from app.models.apod import ApodRecord as APODResponse
from app.models.nasa import EONETEvent, NeoObject

SOURCE_INFO: dict[str, tuple[str, str]] = {
    "APOD": ("Astronomy Picture of the Day", "science.nasa.gov"),
    "NEOWS": ("Near-Earth Object Web Service", "api.nasa.gov"),
    "DONKI": (
        "Space Weather Database Of Notifications, Knowledge, Information",
        "ccmc.gsfc.nasa.gov",
    ),
    "EONET": ("Earth Observatory Natural Event Tracker", "eonet.gsfc.nasa.gov"),
    "NASA_MEDIA": ("NASA Image and Video Library", "images-api.nasa.gov"),
}


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


async def _persist_source_record(
    session: AsyncSession,
    *,
    source_code: str,
    external_id: str,
    source_url: str | None,
    retrieved_at: datetime,
    payload: dict[str, Any],
) -> UUID:
    source_name, base_host = SOURCE_INFO[source_code]
    await session.execute(
        pg_insert(DataSource)
        .values(
            code=source_code,
            display_name=source_name,
            base_host=base_host,
            enabled=True,
            policy={},
        )
        .on_conflict_do_update(
            index_elements=[DataSource.code],
            set_={"display_name": source_name, "base_host": base_host, "enabled": True},
        )
    )

    encoded = _canonical_json(payload)
    record_id = uuid4()
    await session.execute(
        pg_insert(SourceRecord)
        .values(
            id=record_id,
            source_code=source_code,
            external_id=external_id,
            source_url=source_url,
            retrieved_at=retrieved_at,
            payload_hash=hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
            raw_payload=payload,
            schema_version="1",
            normalizer_version="1",
        )
        .on_conflict_do_update(
            index_elements=[SourceRecord.source_code, SourceRecord.external_id],
            set_={
                "source_url": source_url,
                "retrieved_at": retrieved_at,
                "payload_hash": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
                "raw_payload": payload,
                "schema_version": "1",
                "normalizer_version": "1",
            },
        )
    )
    persisted_id = await session.scalar(
        select(SourceRecord.id).where(
            SourceRecord.source_code == source_code,
            SourceRecord.external_id == external_id,
        )
    )
    if persisted_id is None:
        raise RuntimeError("The source record was not persisted.")
    return persisted_id


async def persist_apod(
    session: AsyncSession,
    record: APODResponse,
    retrieved_at: datetime,
) -> UUID:
    payload = record.model_dump(mode="json")
    record_id = await _persist_source_record(
        session,
        source_code="APOD",
        external_id=record.date.isoformat(),
        source_url=str(record.permalink or "https://science.nasa.gov/"),
        retrieved_at=retrieved_at,
        payload=payload,
    )
    await session.execute(
        pg_insert(APODRecord)
        .values(
            source_record_id=record_id,
            apod_date=record.date,
            title=record.title,
            explanation=record.explanation,
            media_type=record.media_type,
            page_url=str(record.permalink or record.url or "https://science.nasa.gov/"),
            media_url=str(record.url) if record.url else None,
            hd_url=str(record.hdurl) if record.hdurl else None,
            alt_text=record.alt,
            credit=record.credit,
            copyright=record.copyright,
        )
        .on_conflict_do_update(
            index_elements=[APODRecord.source_record_id],
            set_={
                "apod_date": record.date,
                "title": record.title,
                "explanation": record.explanation,
                "media_type": record.media_type,
                "page_url": str(record.permalink or record.url or "https://science.nasa.gov/"),
                "media_url": str(record.url) if record.url else None,
                "hd_url": str(record.hdurl) if record.hdurl else None,
                "alt_text": record.alt,
                "credit": record.credit,
                "copyright": record.copyright,
            },
        )
    )
    return record_id


async def persist_neo(
    session: AsyncSession,
    raw: dict[str, Any],
    retrieved_at: datetime,
) -> UUID:
    try:
        record = NeoObject.model_validate(raw)
    except ValidationError as error:
        raise UpstreamError(
            "NEOWS",
            "upstream_schema_error",
            "NeoWs returned a malformed asteroid record.",
            retryable=False,
        ) from error

    source_url = f"https://api.nasa.gov/neo/rest/v1/neo/{record.id}"
    record_id = await _persist_source_record(
        session,
        source_code="NEOWS",
        external_id=record.id,
        source_url=source_url,
        retrieved_at=retrieved_at,
        payload=raw,
    )
    diameter = record.estimated_diameter.get("kilometers", {})
    await session.execute(
        pg_insert(NEOObject)
        .values(
            source_record_id=record_id,
            neo_id=record.id,
            name=record.name,
            absolute_magnitude=_decimal(record.absolute_magnitude_h),
            diameter_min_km=_decimal(diameter.get("estimated_diameter_min")),
            diameter_max_km=_decimal(diameter.get("estimated_diameter_max")),
            potentially_hazardous=record.is_potentially_hazardous_asteroid,
            sentry_object=record.is_sentry_object,
            jpl_url=str(record.nasa_jpl_url) if record.nasa_jpl_url else None,
        )
        .on_conflict_do_update(
            index_elements=[NEOObject.source_record_id],
            set_={
                "neo_id": record.id,
                "name": record.name,
                "absolute_magnitude": _decimal(record.absolute_magnitude_h),
                "diameter_min_km": _decimal(diameter.get("estimated_diameter_min")),
                "diameter_max_km": _decimal(diameter.get("estimated_diameter_max")),
                "potentially_hazardous": record.is_potentially_hazardous_asteroid,
                "sentry_object": record.is_sentry_object,
                "jpl_url": str(record.nasa_jpl_url) if record.nasa_jpl_url else None,
            },
        )
    )

    for approach in record.close_approach_data:
        velocity = _decimal(approach.relative_velocity.get("kilometers_per_second"))
        miss_km = _decimal(approach.miss_distance.get("kilometers"))
        miss_au = _decimal(approach.miss_distance.get("astronomical"))
        epoch = (
            datetime.fromtimestamp(approach.epoch_date_close_approach / 1000, UTC)
            if approach.epoch_date_close_approach is not None
            else None
        )
        await session.execute(
            pg_insert(NEOApproach)
            .values(
                id=uuid4(),
                source_record_id=record_id,
                neo_id=record.id,
                approach_date=approach.close_approach_date,
                epoch_date_close=epoch,
                velocity_km_s=velocity,
                miss_distance_km=miss_km,
                miss_distance_au=miss_au,
                orbiting_body=approach.orbiting_body,
            )
            .on_conflict_do_update(
                index_elements=[
                    NEOApproach.neo_id,
                    NEOApproach.approach_date,
                    NEOApproach.orbiting_body,
                ],
                set_={
                    "source_record_id": record_id,
                    "epoch_date_close": epoch,
                    "velocity_km_s": velocity,
                    "miss_distance_km": miss_km,
                    "miss_distance_au": miss_au,
                },
            )
        )
    return record_id


async def persist_donki(
    session: AsyncSession,
    event_type: str,
    raw: dict[str, Any],
    retrieved_at: datetime,
) -> UUID:
    activity = raw.get("activityID") or raw.get("activityId") or raw.get("id")
    if activity:
        external_id = f"{event_type}:{activity}"
    else:
        external_id = f"{event_type}:{hashlib.sha256(_canonical_json(raw).encode()).hexdigest()}"
    source_url = raw.get("link") if isinstance(raw.get("link"), str) else None
    record_id = await _persist_source_record(
        session,
        source_code="DONKI",
        external_id=external_id,
        source_url=source_url,
        retrieved_at=retrieved_at,
        payload=raw,
    )
    start_time = _datetime(
        raw.get("startTime") or raw.get("eventTime") or raw.get("time21_5") or raw.get("beginTime")
    )
    end_time = _datetime(raw.get("endTime") or raw.get("endTime21_5") or raw.get("endTimeUTC"))
    await session.execute(
        pg_insert(SpaceWeatherEvent)
        .values(
            source_record_id=record_id,
            event_type=event_type,
            activity_id=str(activity) if activity else None,
            start_time=start_time,
            end_time=end_time,
            class_type=str(raw.get("classType") or raw.get("type") or "") or None,
            source_location=str(raw.get("sourceLocation") or "") or None,
            details=raw,
            link=source_url,
        )
        .on_conflict_do_update(
            index_elements=[SpaceWeatherEvent.source_record_id],
            set_={
                "event_type": event_type,
                "activity_id": str(activity) if activity else None,
                "start_time": start_time,
                "end_time": end_time,
                "class_type": str(raw.get("classType") or raw.get("type") or "") or None,
                "source_location": str(raw.get("sourceLocation") or "") or None,
                "details": raw,
                "link": source_url,
            },
        )
    )
    return record_id


async def persist_eonet(
    session: AsyncSession,
    raw: dict[str, Any],
    retrieved_at: datetime,
) -> UUID:
    try:
        event = EONETEvent.model_validate(raw)
    except ValidationError as error:
        raise UpstreamError(
            "EONET",
            "upstream_schema_error",
            "EONET returned a malformed event record.",
            retryable=False,
        ) from error
    record_id = await _persist_source_record(
        session,
        source_code="EONET",
        external_id=event.id,
        source_url=str(event.link) if event.link else None,
        retrieved_at=retrieved_at,
        payload=raw,
    )
    geometry = [item.model_dump(mode="json") for item in event.geometry]
    latest_geometry = event.geometry[-1] if event.geometry else None
    opened_at = event.geometry[0].date if event.geometry else None
    await session.execute(
        pg_insert(EarthEvent)
        .values(
            source_record_id=record_id,
            eonet_id=event.id,
            title=event.title,
            description=event.description,
            opened_at=opened_at,
            closed_at=event.closed,
            categories=[item for item in event.categories],
            sources=[item for item in event.sources],
            geometry=geometry,
            geometry_type=latest_geometry.type if latest_geometry else None,
            magnitude_value=_decimal(latest_geometry.magnitudeValue) if latest_geometry else None,
            magnitude_unit=latest_geometry.magnitudeUnit if latest_geometry else None,
        )
        .on_conflict_do_update(
            index_elements=[EarthEvent.source_record_id],
            set_={
                "eonet_id": event.id,
                "title": event.title,
                "description": event.description,
                "opened_at": opened_at,
                "closed_at": event.closed,
                "categories": [item for item in event.categories],
                "sources": [item for item in event.sources],
                "geometry": geometry,
                "geometry_type": latest_geometry.type if latest_geometry else None,
                "magnitude_value": _decimal(latest_geometry.magnitudeValue)
                if latest_geometry
                else None,
                "magnitude_unit": latest_geometry.magnitudeUnit if latest_geometry else None,
            },
        )
    )
    return record_id


async def persist_media_item(
    session: AsyncSession,
    item: dict[str, Any],
    retrieved_at: datetime,
) -> UUID:
    details = item.get("data")
    if not isinstance(details, list) or not details or not isinstance(details[0], dict):
        raise UpstreamError(
            "NASA_MEDIA",
            "upstream_schema_error",
            "NASA media item metadata is malformed.",
            retryable=False,
        )
    metadata = details[0]
    nasa_id = metadata.get("nasa_id")
    title = metadata.get("title")
    media_type = metadata.get("media_type")
    if (
        not isinstance(nasa_id, str)
        or not nasa_id
        or not isinstance(title, str)
        or not title
        or not isinstance(media_type, str)
        or not media_type
    ):
        raise UpstreamError(
            "NASA_MEDIA",
            "upstream_schema_error",
            "NASA media item is missing required identity fields.",
            retryable=False,
        )
    source_url = f"https://images.nasa.gov/details/{nasa_id}"
    record_id = await _persist_source_record(
        session,
        source_code="NASA_MEDIA",
        external_id=nasa_id,
        source_url=source_url,
        retrieved_at=retrieved_at,
        payload=item,
    )
    creators = [
        value
        for value in (metadata.get("photographer"), metadata.get("secondary_creator"))
        if isinstance(value, str) and value
    ]
    date_created = _datetime(metadata.get("date_created"))
    await session.execute(
        pg_insert(MediaRecord)
        .values(
            source_record_id=record_id,
            nasa_id=nasa_id,
            title=title,
            media_type=media_type,
            date_created=date_created,
            description=metadata.get("description"),
            description_508=metadata.get("description_508"),
            keywords=metadata.get("keywords") if isinstance(metadata.get("keywords"), list) else [],
            creators=creators,
            asset_manifest_url=f"https://images-api.nasa.gov/asset/{nasa_id}",
            detail_url=source_url,
            rights_note=metadata.get("copyright") or metadata.get("rights"),
        )
        .on_conflict_do_update(
            index_elements=[MediaRecord.source_record_id],
            set_={
                "nasa_id": nasa_id,
                "title": title,
                "media_type": media_type,
                "date_created": date_created,
                "description": metadata.get("description"),
                "description_508": metadata.get("description_508"),
                "keywords": metadata.get("keywords")
                if isinstance(metadata.get("keywords"), list)
                else [],
                "creators": creators,
                "asset_manifest_url": f"https://images-api.nasa.gov/asset/{nasa_id}",
                "detail_url": source_url,
                "rights_note": metadata.get("copyright") or metadata.get("rights"),
            },
        )
    )
    return record_id
