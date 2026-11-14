"""Public NASA-backed read endpoints with provenance and database persistence."""

from __future__ import annotations

import asyncio
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import quote_plus, urlsplit

from fastapi import APIRouter, Depends, Query, Request
from fastapi import Path as PathParameter
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.api.dependencies import get_nasa_clients
from app.api.schemas import AsteroidOrbitMapItem, AsteroidOrbitMapRequest, PageResponse
from app.clients.nasa_donki import DONKI_EVENT_TYPES
from app.clients.registry import NASAClients
from app.core.config import Settings, get_settings
from app.core.errors import AppError, UpstreamError
from app.core.rate_limit import limiter
from app.db.dependencies import get_db_session
from app.db.models import APODRecord, SourceRecord, SpaceWeatherEvent
from app.models.apod import ApodRecord
from app.models.nasa import EONETEvent, NeoObject
from app.services.ingestion import (
    persist_apod,
    persist_donki,
    persist_eonet,
    persist_media_item,
    persist_neo,
)

router = APIRouter(prefix="/api/v1", tags=["NASA data"])
PUBLIC_PAGE_LIMIT = 100
APOD_PAGE_LIMIT = 25


def _public_url(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or (host != "nasa.gov" and not host.endswith(".nasa.gov")):
        return None
    if parsed.username or parsed.password:
        return None
    return value


def _safe_https_url(value: Any) -> str | None:
    """Allow a safe external HTTPS link without trusting upstream URL input."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    return value


def _eonet_wms_layer(
    layers: list[dict[str, Any]], observed_at: datetime | None
) -> dict[str, Any] | None:
    """Select a known NASA GIBS WMS overlay from the EONET category layer list."""
    supported_hosts = {"map2.vis.earthdata.nasa.gov", "map1.vis.earthdata.nasa.gov"}
    candidates: list[dict[str, Any]] = []
    for layer in layers:
        if layer.get("serviceTypeId") != "WMS_1_1_1":
            continue
        service_url = _safe_https_url(layer.get("serviceUrl"))
        name = layer.get("name")
        if not service_url or urlsplit(service_url).hostname not in supported_hosts:
            continue
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", name):
            continue
        parameters = layer.get("parameters")
        settings = (
            parameters[0]
            if isinstance(parameters, list)
            and parameters
            and isinstance(parameters[0], dict)
            else {}
        )
        image_format = (
            settings.get("FORMAT")
            if settings.get("FORMAT") in {"image/png", "image/jpeg"}
            else "image/png"
        )
        candidates.append({"service_url": service_url, "name": name, "format": image_format})

    priorities = (
        "VIIRS_SNPP_Fires_375m_Day",
        "MODIS_Fires_All",
        "VIIRS_SNPP_Fires_375m_Night",
        "VIIRS_SNPP_CorrectedReflectance_TrueColor",
        "MODIS_Terra_CorrectedReflectance_TrueColor",
    )
    selected = next(
        (item for preferred in priorities for item in candidates if item["name"] == preferred),
        None,
    )
    selected = selected or next(
        (item for item in candidates if "CorrectedReflectance_TrueColor" in item["name"]),
        None,
    )
    selected = selected or (candidates[0] if candidates else None)
    if selected is None:
        return None
    return {
        **selected,
        "date": observed_at.date().isoformat() if observed_at else None,
        "attribution": "NASA EOSDIS GIBS imagery via EONET category layers",
    }


def _eonet_news_query(title: str, category_ids: list[str]) -> str:
    """Build a location-and-category query, which tolerates press headline variations."""
    category_terms = {
        "wildfires": '(wildfire OR wildfires OR fire)',
        "floods": '(flood OR flooding)',
        "severeStorms": '(storm OR hurricane OR tornado)',
        "volcanoes": '(volcano OR eruption)',
        "earthquakes": '(earthquake OR quake)',
        "landslides": '(landslide OR mudslide)',
        "drought": '(drought OR dry spell)',
        "dustHaze": '(dust storm OR haze)',
        "seaLakeIce": '(sea ice OR lake ice)',
        "snow": '(snowstorm OR blizzard)',
    }
    terms = next((category_terms[key] for key in category_ids if key in category_terms), "")
    chunks = [re.sub(r"[^A-Za-z0-9 '-]", " ", part).strip() for part in title.split(",")]
    location = " ".join(part for part in chunks[-2:] if part).strip()
    if location and terms:
        return f'"{location}" {terms}'
    return re.sub(r"[^A-Za-z0-9 '-]", " ", title).strip()


def _provenance(
    source: str, upstream_id: str, source_url: Any, retrieved_at: datetime
) -> dict[str, Any]:
    return {
        "source": source,
        "upstream_id": upstream_id,
        "source_url": _public_url(source_url),
        "retrieved_at": retrieved_at,
    }


def _check_dates(
    start_date: date | None, end_date: date | None, max_days: int | None = None
) -> None:
    if start_date and end_date and start_date > end_date:
        raise AppError(
            "invalid_date_range",
            "Invalid date range",
            "The start date must be on or before the end date.",
            422,
        )
    if start_date and end_date and max_days is not None and (end_date - start_date).days > max_days:
        raise AppError(
            "date_range_too_large",
            "Date range too large",
            "The requested date range exceeds the supported limit.",
            422,
        )


async def _check_public_limit(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    client_host = request.client.host if request.client else "unknown"
    await limiter.check(f"public:{client_host}", settings.public_rate_limit_per_minute)


def _page_bounds(page: int, page_size: int, *, maximum: int = PUBLIC_PAGE_LIMIT) -> tuple[int, int]:
    if page < 1 or page_size < 1 or page_size > maximum:
        raise AppError(
            "invalid_pagination",
            "Invalid pagination",
            "The requested page or page size is invalid.",
            422,
        )
    return (page - 1) * page_size, page * page_size


def _page(
    items: list[dict[str, Any]],
    *,
    page: int,
    page_size: int,
    total: int,
    retrieved_at: datetime,
) -> dict[str, Any]:
    start, end = _page_bounds(page, page_size)
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "retrieved_at": retrieved_at,
        "freshness": "current",
    }


def _apod_item(record: ApodRecord, retrieved_at: datetime) -> dict[str, Any]:
    item = record.model_dump(mode="json")
    item.pop("basic_html", None)
    item.pop("basic_html_url", None)
    item["source_url"] = _public_url(str(record.permalink or record.url or ""))
    item["retrieved_at"] = retrieved_at
    item["provenance"] = _provenance(
        "APOD", record.date.isoformat(), record.permalink, retrieved_at
    )
    return item


@router.get("/astronomy/apod", response_model=PageResponse[dict[str, Any]])
async def get_apod(
    request: Request,
    apod_date: date | None = Query(default=None, alias="date"),
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=APOD_PAGE_LIMIT),
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    if apod_date and (start_date or end_date):
        raise AppError(
            "conflicting_date_filters",
            "Invalid date filter",
            "Use either a single date or a date range.",
            422,
        )
    _check_dates(start_date, end_date)
    retrieved_at = datetime.now(UTC)
    if apod_date:
        record = await clients.apod.get_by_date(apod_date)
        if record is None:
            return _page([], page=page, page_size=page_size, total=0, retrieved_at=retrieved_at)
        records = [record]
    else:
        records = await clients.apod.search(
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
    for record in records:
        await persist_apod(session, record, retrieved_at)
    items = [_apod_item(record, retrieved_at) for record in records]
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": len(items),
        "retrieved_at": retrieved_at,
        "freshness": "current",
    }


def _media_item(raw: dict[str, Any], retrieved_at: datetime) -> dict[str, Any]:
    data = raw.get("data")
    metadata: dict[str, Any] = {}
    if isinstance(data, list) and data and isinstance(data[0], dict):
        metadata = data[0]
    nasa_id = str(metadata.get("nasa_id") or "")
    title = str(metadata.get("title") or "Untitled NASA media item")
    media_kind = str(metadata.get("media_type") or "unknown")
    links_value = raw.get("links")
    links = links_value if isinstance(links_value, list) else []
    thumbnail = next(
        (
            _public_url(link.get("href"))
            for link in links
            if isinstance(link, dict) and link.get("rel") == "preview"
        ),
        None,
    )
    detail_url = f"https://images.nasa.gov/details/{nasa_id}" if nasa_id else None
    return {
        "nasa_id": nasa_id,
        "title": title,
        "media_type": media_kind,
        "date_created": metadata.get("date_created"),
        "description": metadata.get("description"),
        "description_508": metadata.get("description_508"),
        "thumbnail_url": thumbnail,
        "detail_url": detail_url,
        "asset_manifest_url": f"https://images-api.nasa.gov/asset/{nasa_id}" if nasa_id else None,
        "creators": [
            metadata[name]
            for name in ("photographer", "secondary_creator")
            if isinstance(metadata.get(name), str)
        ],
        "rights_note": metadata.get("copyright") or metadata.get("rights"),
        "keywords": metadata.get("keywords") if isinstance(metadata.get("keywords"), list) else [],
        "source_url": detail_url,
        "retrieved_at": retrieved_at,
        "provenance": _provenance("NASA_MEDIA", nasa_id, detail_url, retrieved_at),
    }


@router.get("/astronomy/apod/{apod_date}")
async def get_apod_by_date(
    apod_date: date,
    request: Request,
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    retrieved_at = datetime.now(UTC)
    record = await clients.apod.get_by_date(apod_date)
    if record is None:
        raise AppError("not_found", "Not found", "No APOD record exists for that date.", 404)
    await persist_apod(session, record, retrieved_at)
    return _apod_item(record, retrieved_at)


@router.get("/astronomy/records", response_model=PageResponse[dict[str, Any]])
async def search_apod_records(
    q: str | None = Query(default=None, max_length=200),
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=APOD_PAGE_LIMIT),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    _check_dates(start_date, end_date)
    _page_bounds(page, page_size, maximum=APOD_PAGE_LIMIT)
    predicates: list[ColumnElement[bool]] = []
    if q:
        predicates.append(APODRecord.title.ilike(f"%{q.strip()}%"))
    if start_date:
        predicates.append(APODRecord.apod_date >= start_date)
    if end_date:
        predicates.append(APODRecord.apod_date <= end_date)
    statement = (
        select(APODRecord, SourceRecord)
        .join(SourceRecord, APODRecord.source_record_id == SourceRecord.id)
        .where(*predicates)
    )
    count = await session.scalar(select(func.count()).select_from(APODRecord).where(*predicates))
    rows = (
        await session.execute(
            statement.order_by(APODRecord.apod_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    total = int(count or 0)
    items = []
    for apod, source_record in rows:
        items.append(
            {
                "date": apod.apod_date.isoformat(),
                "title": apod.title,
                "explanation": apod.explanation,
                "media_type": apod.media_type,
                "permalink": apod.page_url,
                "url": apod.media_url,
                "hdurl": apod.hd_url,
                "alt": apod.alt_text,
                "credit": apod.credit,
                "copyright": apod.copyright,
                "source_url": _public_url(source_record.source_url),
                "retrieved_at": source_record.retrieved_at,
                "provenance": _provenance(
                    "APOD",
                    source_record.external_id,
                    source_record.source_url,
                    source_record.retrieved_at,
                ),
            }
        )
    now = datetime.now(UTC)
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "retrieved_at": now,
        "freshness": "current",
    }


def _neo_item(raw: dict[str, Any], retrieved_at: datetime) -> dict[str, Any]:
    record = NeoObject.model_validate(raw)
    diameter = record.estimated_diameter.get("kilometers", {})
    approaches = []
    for approach in record.close_approach_data:
        velocity = approach.relative_velocity.get("kilometers_per_second")
        miss_distance = approach.miss_distance.get("kilometers")
        try:
            velocity_value = float(velocity) if velocity is not None else None
            distance_value = float(miss_distance) if miss_distance is not None else None
        except ValueError:
            velocity_value = None
            distance_value = None
        approaches.append(
            {
                "date": approach.close_approach_date.isoformat(),
                "relative_velocity_km_s": velocity_value,
                "miss_distance_km": distance_value,
                "orbiting_body": approach.orbiting_body,
            }
        )
    source_url = _public_url(str(record.nasa_jpl_url) if record.nasa_jpl_url else "")
    return {
        "neo_id": record.id,
        "name": record.name,
        "absolute_magnitude": record.absolute_magnitude_h,
        "potentially_hazardous": record.is_potentially_hazardous_asteroid,
        "sentry_object": record.is_sentry_object,
        "estimated_diameter_km": {
            "min": diameter.get("estimated_diameter_min"),
            "max": diameter.get("estimated_diameter_max"),
        },
        "close_approaches": approaches,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "provenance": _provenance("NEOWS", record.id, source_url, retrieved_at),
    }


@router.get("/asteroids", response_model=PageResponse[dict[str, Any]])
async def list_asteroids(
    request: Request,
    q: str | None = Query(default=None, max_length=100),
    close_approach_start: date | None = None,
    close_approach_end: date | None = None,
    potentially_hazardous: bool | None = None,
    minimum_diameter_km: float | None = Query(default=None, ge=0),
    maximum_diameter_km: float | None = Query(default=None, ge=0),
    sort: str = Query(default="close_approach", pattern="^(close_approach|name|diameter)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=PUBLIC_PAGE_LIMIT),
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    _check_dates(close_approach_start, close_approach_end, max_days=6)
    if (
        minimum_diameter_km is not None
        and maximum_diameter_km is not None
        and minimum_diameter_km > maximum_diameter_km
    ):
        raise AppError(
            "invalid_diameter_range",
            "Invalid diameter range",
            "The minimum diameter must be on or below the maximum diameter.",
            422,
        )
    today = datetime.now(UTC).date()
    start = close_approach_start or (
        close_approach_end - timedelta(days=6) if close_approach_end else today
    )
    end = close_approach_end or (start + timedelta(days=6))
    payload = await clients.neows.feed(start, end)
    groups = payload.get("near_earth_objects", {})
    if not isinstance(groups, dict):
        raise UpstreamError(
            "NEOWS", "upstream_schema_error", "NeoWs returned an unexpected feed.", retryable=False
        )
    retrieved_at = datetime.now(UTC)
    raw_items: list[dict[str, Any]] = []
    for values in groups.values():
        if not isinstance(values, list):
            raise UpstreamError(
                "NEOWS",
                "upstream_schema_error",
                "NeoWs returned a malformed date group.",
                retryable=False,
            )
        for item in values:
            if not isinstance(item, dict):
                raise UpstreamError(
                    "NEOWS",
                    "upstream_schema_error",
                    "NeoWs returned a malformed asteroid.",
                    retryable=False,
                )
            raw_items.append(item)
            await persist_neo(session, item, retrieved_at)
    items = [_neo_item(item, retrieved_at) for item in raw_items]
    if q:
        normalized_query = q.casefold().strip()
        items = [
            item
            for item in items
            if normalized_query in item["name"].casefold() or normalized_query in item["neo_id"]
        ]
    if potentially_hazardous is not None:
        items = [item for item in items if item["potentially_hazardous"] is potentially_hazardous]
    if minimum_diameter_km is not None:
        items = [
            item
            for item in items
            if item["estimated_diameter_km"]["max"] is not None
            and item["estimated_diameter_km"]["max"] >= minimum_diameter_km
        ]
    if maximum_diameter_km is not None:
        items = [
            item
            for item in items
            if item["estimated_diameter_km"]["min"] is not None
            and item["estimated_diameter_km"]["min"] <= maximum_diameter_km
        ]
    if sort == "name":
        items.sort(key=lambda item: item["name"].casefold())
    elif sort == "diameter":
        items.sort(key=lambda item: item["estimated_diameter_km"]["max"] or 0, reverse=True)
    else:
        items.sort(
            key=lambda item: (
                item["close_approaches"][0]["date"] if item["close_approaches"] else "9999-12-31"
            )
        )
    return _page(items, page=page, page_size=page_size, total=len(items), retrieved_at=retrieved_at)


@router.get("/asteroids/{neo_id}")
async def get_asteroid(
    neo_id: str,
    request: Request,
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    raw = await clients.neows.get(neo_id)
    retrieved_at = datetime.now(UTC)
    payload = raw.model_dump(mode="json")
    await persist_neo(session, payload, retrieved_at)
    return _neo_item(payload, retrieved_at)


@router.get("/asteroids/{neo_id}/orbit")
async def get_asteroid_orbit(
    neo_id: str,
    clients: NASAClients = Depends(get_nasa_clients),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    """Return a JPL SBDB solution and geocentric Horizons path around its nearest approach."""
    if not neo_id.isdigit() or len(neo_id) > 20:
        raise AppError(
            "invalid_neo_id",
            "Invalid asteroid ID",
            "The asteroid ID must contain up to 20 digits.",
            422,
        )
    if clients.jpl is None:
        raise AppError(
            "jpl_unavailable",
            "Orbit data unavailable",
            "JPL orbit data is not configured for this service.",
            503,
        )
    raw = await clients.neows.get(neo_id)
    today = datetime.now(UTC).date()
    approaches = [
        item.close_approach_date
        for item in raw.close_approach_data
        if item.close_approach_date
    ]
    target_date = (
        min(approaches, key=lambda item: abs((item - today).days)) if approaches else today
    )
    start, end = target_date - timedelta(days=7), target_date + timedelta(days=7)
    trajectory = await clients.jpl.trajectory(raw.name, start, end)
    return {"neo_id": neo_id, "name": raw.name, **trajectory}


@router.post("/asteroids/orbit-map")
async def get_asteroid_orbit_map(
    body: AsteroidOrbitMapRequest,
    clients: NASAClients = Depends(get_nasa_clients),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    """Load a common-time-window set of Earth-relative Horizons paths for the visible NEOs."""
    jpl_client = clients.jpl
    if jpl_client is None:
        raise AppError(
            "jpl_unavailable",
            "Orbit data unavailable",
            "JPL orbit data is not configured for this service.",
            503,
        )

    today = datetime.now(UTC).date()
    start = today - timedelta(days=body.window_days)
    end = today + timedelta(days=body.window_days)
    earth_points = await jpl_client.vectors("399", start, end, center="500@10")
    earth_by_epoch = {round(point["jd_tdb"], 6): point for point in earth_points}
    semaphore = asyncio.Semaphore(4)

    async def load_object(item: AsteroidOrbitMapItem) -> dict[str, Any] | None:
        async with semaphore:
            heliocentric = None
            # Prefer the human-readable designation, then retry with the
            # catalogue's numeric NEO ID. Horizons resolves both forms, and
            # the ID fallback covers provisional designations that its name
            # resolver may not recognize consistently.
            for target in dict.fromkeys((item.name, item.neo_id)):
                try:
                    heliocentric = await jpl_client.vectors_for_designation(
                        target, start, end, center="500@10"
                    )
                    break
                except (UpstreamError, ValueError):
                    continue
            if heliocentric is None:
                return None
        points = []
        for point in heliocentric:
            earth = earth_by_epoch.get(round(point["jd_tdb"], 6))
            if earth is None:
                continue
            x = point["x_au"] - earth["x_au"]
            y = point["y_au"] - earth["y_au"]
            z = point["z_au"] - earth["z_au"]
            points.append({
                "jd_tdb": point["jd_tdb"],
                "date": point["date"],
                "x_au": x,
                "y_au": y,
                "z_au": z,
                "distance_au": (x * x + y * y + z * z) ** 0.5,
            })
        if len(points) < 2:
            return None
        return {
            "neo_id": item.neo_id,
            "name": item.name,
            "diameter_km": item.diameter_km,
            "potentially_hazardous": item.potentially_hazardous,
            "points": points,
        }

    results = await asyncio.gather(*(load_object(item) for item in body.objects))
    objects = [item for item in results if item is not None]
    successful_ids = {item["neo_id"] for item in objects}
    unavailable = [
        {"neo_id": item.neo_id, "name": item.name}
        for item in body.objects
        if item.neo_id not in successful_ids
    ]
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "window_days": body.window_days,
        "sample_interval_hours": 6,
        "center": "Earth geocenter",
        "reference_plane": "Ecliptic",
        "times": [{"jd_tdb": item["jd_tdb"], "date": item["date"]} for item in earth_points],
        "objects": objects,
        "unavailable": unavailable,
    }


@router.get("/space-weather/events", response_model=PageResponse[dict[str, Any]])
async def list_space_weather(
    request: Request,
    event_type: str = Query(default="notifications", alias="type"),
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=PUBLIC_PAGE_LIMIT),
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    _check_dates(start_date, end_date, max_days=29)
    if event_type not in DONKI_EVENT_TYPES:
        raise AppError(
            "invalid_event_type",
            "Invalid event type",
            "The requested DONKI event type is not supported.",
            422,
        )
    end = end_date or datetime.now(UTC).date()
    start = start_date or (end - timedelta(days=29))
    raw_events = await clients.donki.events(event_type, start, end)
    retrieved_at = datetime.now(UTC)
    items = []
    for raw in raw_events:
        persisted_id = await persist_donki(session, event_type, raw, retrieved_at)
        external_id = await session.scalar(
            select(SourceRecord.external_id).where(SourceRecord.id == persisted_id)
        )
        event_id = str(raw.get("activityID") or raw.get("messageID") or raw.get("activityId") or "")
        source_url = _public_url(raw.get("link") or raw.get("messageURL"))
        event_label = str(raw.get("type") or raw.get("eventType") or event_type)
        title = str(raw.get("name") or raw.get("title") or event_label)
        items.append(
            {
                "event_type": event_label,
                "event_id": event_id or None,
                "activity_id": str(raw.get("activityID") or raw.get("activityId") or "") or None,
                "start_time": raw.get("startTime")
                or raw.get("eventTime")
                or raw.get("messageIssueTime"),
                "end_time": raw.get("endTime"),
                "title": title,
                "summary": raw.get("messageBody") or raw.get("note") or raw.get("link"),
                "source_url": source_url,
                "details": raw,
                "retrieved_at": retrieved_at,
                "provenance": _provenance(
                    "DONKI", str(external_id or event_id or event_type), source_url, retrieved_at
                ),
            }
        )
    return _page(items, page=page, page_size=page_size, total=len(items), retrieved_at=retrieved_at)


@router.get("/space-weather/events/{record_id}")
async def get_space_weather_event(
    record_id: str = PathParameter(pattern=r"^[A-Za-z0-9:_-]{1,300}$"),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    """Read a stored DONKI event by its persisted source identity."""

    source = await session.scalar(
        select(SourceRecord).where(
            SourceRecord.source_code == "DONKI",
            SourceRecord.external_id == record_id,
        )
    )
    if source is None:
        raise AppError("not_found", "Not found", "No stored DONKI event exists with that ID.", 404)
    event = await session.scalar(
        select(SpaceWeatherEvent).where(SpaceWeatherEvent.source_record_id == source.id)
    )
    if event is None:
        raise AppError("not_found", "Not found", "No stored DONKI event exists with that ID.", 404)
    payload = source.raw_payload if isinstance(source.raw_payload, dict) else {}
    event_id = (
        payload.get("activityID")
        or payload.get("messageID")
        or payload.get("activityId")
        or event.activity_id
        or source.external_id
    )
    summary = payload.get("messageBody") or payload.get("note")
    if not isinstance(summary, str):
        summary = None
    source_url = _public_url(source.source_url)
    return {
        "event_type": event.event_type,
        "event_id": str(event_id),
        "activity_id": event.activity_id,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "class_type": event.class_type,
        "source_location": event.source_location,
        "title": event.event_type,
        "summary": summary[:4000] if summary else None,
        "source_url": source_url,
        "retrieved_at": source.retrieved_at,
        "provenance": _provenance("DONKI", source.external_id, source_url, source.retrieved_at),
    }


@router.get("/space-weather/summary")
async def space_weather_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    """Summarize already stored DONKI records without making extra NASA requests."""

    end = end_date or datetime.now(UTC).date()
    start = start_date or (end - timedelta(days=29))
    _check_dates(start, end, max_days=365)
    counts = (
        await session.execute(
            select(SpaceWeatherEvent.event_type, func.count())
            .where(
                SpaceWeatherEvent.start_time >= datetime.combine(start, datetime.min.time(), UTC),
                SpaceWeatherEvent.start_time
                < datetime.combine(end + timedelta(days=1), datetime.min.time(), UTC),
            )
            .group_by(SpaceWeatherEvent.event_type)
            .order_by(SpaceWeatherEvent.event_type)
        )
    ).all()
    last_retrieved = await session.scalar(
        select(func.max(SourceRecord.retrieved_at))
        .join(SpaceWeatherEvent, SpaceWeatherEvent.source_record_id == SourceRecord.id)
        .where(
            SpaceWeatherEvent.start_time >= datetime.combine(start, datetime.min.time(), UTC),
            SpaceWeatherEvent.start_time
            < datetime.combine(end + timedelta(days=1), datetime.min.time(), UTC),
        )
    )
    now = datetime.now(UTC)
    freshness = (
        "unknown"
        if last_retrieved is None
        else "current"
        if (now - last_retrieved).total_seconds() <= 86_400
        else "stale"
    )
    return {
        "start_date": start,
        "end_date": end,
        "total": sum(int(count) for _, count in counts),
        "by_type": {event_type: int(count) for event_type, count in counts},
        "last_retrieved_at": last_retrieved,
        "retrieved_at": now,
        "freshness": freshness,
        "coverage": "Stored DONKI records only; no upstream request was made for this summary.",
    }


def _parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    try:
        values = tuple(float(part.strip()) for part in value.split(","))
    except ValueError:
        raise AppError(
            "invalid_bbox",
            "Invalid bounding box",
            "The bounding box must contain four numbers.",
            422,
        ) from None
    if len(values) != 4:
        raise AppError(
            "invalid_bbox",
            "Invalid bounding box",
            "The bounding box must contain four numbers.",
            422,
        )
    return (values[0], values[1], values[2], values[3])


@router.get("/earth-events", response_model=PageResponse[dict[str, Any]])
async def list_earth_events(
    request: Request,
    category: str | None = Query(default=None, max_length=80),
    status: str = Query(default="open", pattern="^(open|closed|all)$"),
    start: date | None = None,
    end: date | None = None,
    bbox: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=PUBLIC_PAGE_LIMIT),
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    _check_dates(start, end)
    bounds = _parse_bbox(bbox)
    upstream_limit = min(1000, page * page_size)
    response = await clients.eonet.events(
        category=category.strip() if category else None,
        status=status,
        start_date=start,
        end_date=end,
        bbox=bounds,
        limit=upstream_limit,
    )
    raw_events = response.get("events")
    if not isinstance(raw_events, list):
        raise UpstreamError(
            "EONET",
            "upstream_schema_error",
            "EONET returned an unexpected event list.",
            retryable=False,
        )
    retrieved_at = datetime.now(UTC)
    items = []
    for raw in raw_events:
        if not isinstance(raw, dict):
            raise UpstreamError(
                "EONET",
                "upstream_schema_error",
                "EONET returned a malformed event.",
                retryable=False,
            )
        await persist_eonet(session, raw, retrieved_at)
        try:
            event = EONETEvent.model_validate(raw)
        except ValidationError as error:
            raise UpstreamError(
                "EONET",
                "upstream_schema_error",
                "EONET returned a malformed event.",
                retryable=False,
            ) from error
        source_url = _public_url(str(event.link) if event.link else None)
        item = event.model_dump(mode="json")
        item.update(
            {
                "event_id": event.id,
                "status": "closed" if event.closed else "open",
                "opened_at": event.geometry[0].date if event.geometry else None,
                "closed_at": event.closed,
                "source_url": source_url,
                "retrieved_at": retrieved_at,
                "provenance": _provenance("EONET", event.id, source_url, retrieved_at),
            }
        )
        items.append(item)
    count_value = response.get("count")
    total = count_value if isinstance(count_value, int) else len(items)
    return _page(items, page=page, page_size=page_size, total=total, retrieved_at=retrieved_at)


@router.get("/earth-events/{event_id}")
async def get_earth_event(
    event_id: str,
    request: Request,
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    event = await clients.eonet.get(event_id)
    retrieved_at = datetime.now(UTC)
    raw = event.model_dump(mode="json")
    await persist_eonet(session, raw, retrieved_at)
    source_url = _public_url(str(event.link) if event.link else None)
    item = raw
    item.update(
        {
            "event_id": event.id,
            "status": "closed" if event.closed else "open",
            "opened_at": event.geometry[0].date if event.geometry else None,
            "closed_at": event.closed,
            "source_url": source_url,
            "retrieved_at": retrieved_at,
            "provenance": _provenance("EONET", event.id, source_url, retrieved_at),
        }
    )
    return item


@router.get("/earth-events/{event_id}/coverage")
async def get_earth_event_coverage(
    event_id: str = PathParameter(pattern=r"^[A-Za-z0-9._-]{1,100}$"),
    clients: NASAClients = Depends(get_nasa_clients),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    """Combine the selected EONET event with NASA imagery and related news links."""
    event = await clients.eonet.get(event_id)
    category_ids = [
        str(category.get("id"))
        for category in event.categories
        if isinstance(category, dict) and category.get("id")
    ]
    category_titles = [
        str(category.get("title"))
        for category in event.categories
        if isinstance(category, dict) and category.get("title")
    ]
    observed_at = event.geometry[-1].date if event.geometry else None

    async def load_layers() -> list[dict[str, Any]]:
        for category_id in category_ids:
            try:
                layers = await clients.eonet.layers(category_id)
                if layers:
                    return layers
            except (UpstreamError, ValueError):
                continue
        return []

    async def load_nasa_images() -> list[dict[str, Any]]:
        queries = [event.title]
        location_parts = [part.strip() for part in event.title.split(",")[-2:] if part.strip()]
        if category_titles and location_parts:
            queries.append(" ".join((category_titles[0], *location_parts)))
        for query in dict.fromkeys(queries):
            try:
                response = await clients.media.search(
                    query=query,
                    media_type="image",
                    page=1,
                    page_size=6,
                )
                collection = response.get("collection") if isinstance(response, dict) else None
                raw_items = collection.get("items") if isinstance(collection, dict) else None
                retrieved_at = datetime.now(UTC)
                images = []
                for raw in raw_items if isinstance(raw_items, list) else []:
                    if not isinstance(raw, dict):
                        continue
                    image = _media_item(raw, retrieved_at)
                    if image.get("thumbnail_url") and image.get("nasa_id"):
                        images.append(image)
                if images:
                    return images
            except (UpstreamError, ValueError):
                continue
        return []

    async def load_news() -> list[dict[str, Any]]:
        if clients.gdelt is None:
            return []
        try:
            query = _eonet_news_query(event.title, category_ids)
            articles = await clients.gdelt.search(query, exact_phrase=False)
        except (UpstreamError, ValueError):
            return []
        safe_articles = []
        for article in articles:
            url = _safe_https_url(article.get("url"))
            if not url:
                continue
            safe_articles.append({
                **article,
                "url": url,
                "image_url": _safe_https_url(article.get("image_url")),
            })
        return safe_articles

    layers, nasa_images, related_articles = await asyncio.gather(
        load_layers(), load_nasa_images(), load_news()
    )
    sources = [
        {"id": str(source.get("id") or "Event source"), "url": _safe_https_url(source.get("url"))}
        for source in event.sources
        if isinstance(source, dict) and _safe_https_url(source.get("url"))
    ]
    status = "closed" if event.closed else "open"
    return {
        "event_id": event.id,
        "title": event.title,
        "description": event.description,
        "status": status,
        "categories": category_titles,
        "observed_at": observed_at,
        "eonet_url": _public_url(str(event.link) if event.link else None),
        "sources": sources,
        "satellite_imagery": _eonet_wms_layer(layers, observed_at),
        "nasa_images": nasa_images,
        "related_articles": related_articles,
        "news_search_url": f"https://news.google.com/search?q={quote_plus(event.title)}",
        "retrieved_at": datetime.now(UTC),
    }


@router.get("/media", response_model=PageResponse[dict[str, Any]])
async def search_media(
    request: Request,
    q: str = Query(min_length=1, max_length=200),
    media_type: str | None = Query(default=None, pattern="^(image|video|audio)$"),
    year_start: int | None = Query(default=None, ge=1900, le=2200),
    year_end: int | None = Query(default=None, ge=1900, le=2200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=PUBLIC_PAGE_LIMIT),
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    if year_start is not None and year_end is not None and year_start > year_end:
        raise AppError(
            "invalid_year_range",
            "Invalid year range",
            "The starting year must not be later than the ending year.",
            422,
        )
    response = await clients.media.search(
        query=q.strip(),
        media_type=media_type,
        year_start=year_start,
        year_end=year_end,
        page=page,
        page_size=page_size,
    )
    collection = response.get("collection") if isinstance(response, dict) else None
    raw_items = collection.get("items") if isinstance(collection, dict) else None
    if not isinstance(raw_items, list):
        raise UpstreamError(
            "NASA_MEDIA",
            "upstream_schema_error",
            "NASA media returned an unexpected result list.",
            retryable=False,
        )
    retrieved_at = datetime.now(UTC)
    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise UpstreamError(
                "NASA_MEDIA",
                "upstream_schema_error",
                "NASA media returned a malformed item.",
                retryable=False,
            )
        await persist_media_item(session, raw, retrieved_at)
        items.append(_media_item(raw, retrieved_at))
    result_metadata = collection.get("metadata", {}) if isinstance(collection, dict) else {}
    total = result_metadata.get("total_hits") if isinstance(result_metadata, dict) else None
    return _page(
        items,
        page=page,
        page_size=page_size,
        total=total if isinstance(total, int) else len(items),
        retrieved_at=retrieved_at,
    )


router.add_api_route(
    "/media/search",
    search_media,
    methods=["GET"],
    include_in_schema=False,
)


@router.get("/media/{nasa_id}")
async def get_media_item(
    nasa_id: str = PathParameter(pattern=r"^[A-Za-z0-9._-]{1,100}$"),
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
    _limited: None = Depends(_check_public_limit),
) -> dict[str, Any]:
    stored = await session.scalar(
        select(SourceRecord).where(
            SourceRecord.source_code == "NASA_MEDIA",
            SourceRecord.external_id == nasa_id,
        )
    )
    if stored is not None:
        return _media_item(stored.raw_payload, stored.retrieved_at)
    response = await clients.media.search(nasa_id=nasa_id, page=1, page_size=1)
    collection = response.get("collection") if isinstance(response, dict) else None
    raw_items = collection.get("items") if isinstance(collection, dict) else None
    raw = raw_items[0] if isinstance(raw_items, list) and raw_items else None
    if not isinstance(raw, dict):
        raise AppError("not_found", "Not found", "No NASA media item exists with that ID.", 404)
    retrieved_at = datetime.now(UTC)
    await persist_media_item(session, raw, retrieved_at)
    return _media_item(raw, retrieved_at)


__all__ = ["router"]
