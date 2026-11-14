"""Authenticated, owner-scoped workspace and operations endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_nasa_clients
from app.clients.registry import NASAClients
from app.core.auth import UserContext, get_optional_user, require_admin, require_user
from app.core.config import Settings, get_settings
from app.core.errors import AppError, FeatureUnavailableError
from app.core.rate_limit import limiter
from app.db.dependencies import get_db_session
from app.db.models import (
    AIReport,
    AuditEvent,
    DataSource,
    IngestionJob,
    ReportEvidence,
    ResearchConversation,
    SavedRecord,
    SourceRecord,
    UserAccount,
)
from app.services.ingestion import persist_neo

router = APIRouter(prefix="/api/v1", tags=["account and workspace"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["administration"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SavedRecordCreate(StrictModel):
    source_code: Literal["APOD", "NEOWS", "DONKI", "EONET", "NASA_MEDIA"]
    upstream_id: str = Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9._:-]+$")


class ConversationCreate(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)


class ConversationMessageCreate(StrictModel):
    content: str = Field(min_length=1, max_length=8000)


class ReportCreate(StrictModel):
    question: str = Field(min_length=1, max_length=8000)
    title: str | None = Field(default=None, min_length=1, max_length=255)


class NeoComparisonRequest(StrictModel):
    neo_ids: list[str] = Field(min_length=2, max_length=10)

    @field_validator("neo_ids")
    @classmethod
    def validate_neo_ids(cls, values: list[str]) -> list[str]:
        if any(not value.isdigit() or len(value) > 20 for value in values):
            raise ValueError("Each asteroid identifier must contain at most 20 digits.")
        if len(set(values)) != len(values):
            raise ValueError("Asteroid identifiers must be unique.")
        return values


@router.get("/auth/session")
async def auth_session(
    user: UserContext | None = Depends(get_optional_user),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Expose only the current browser's safe authentication mode and identity."""

    return {
        "authenticated": user is not None,
        "development_identity_enabled": settings.app_env == "development"
        and settings.dev_auth_enabled,
        "oidc_configured": bool(settings.oidc_issuer_url and settings.oidc_audience),
        "user": (
            {"subject": user.subject, "is_development_identity": user.is_development_identity}
            if user
            else None
        ),
    }


async def _account_for(
    session: AsyncSession,
    user: UserContext,
) -> UserAccount:
    """Upsert the account key derived only from the validated auth subject."""

    result = await session.execute(
        pg_insert(UserAccount)
        .values(oidc_subject=user.subject, last_seen_at=datetime.now(UTC))
        .on_conflict_do_update(
            index_elements=[UserAccount.oidc_subject],
            set_={"last_seen_at": func.now()},
        )
        .returning(UserAccount)
    )
    account = result.scalar_one()
    await session.flush()
    return account


def _nasa_source_url(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if not value.startswith("https://"):
        return None
    from urllib.parse import urlsplit

    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "nasa.gov" or host.endswith(".nasa.gov")):
        return None
    if parsed.username or parsed.password:
        return None
    return value


def _saved_record_summary(source: SourceRecord) -> dict[str, Any]:
    payload = source.raw_payload if isinstance(source.raw_payload, dict) else {}
    metadata: dict[str, Any] = {}
    if source.source_code == "NASA_MEDIA":
        values = payload.get("data")
        if isinstance(values, list) and values and isinstance(values[0], dict):
            metadata = values[0]
    elif source.source_code == "EONET":
        metadata = payload
    elif source.source_code == "DONKI":
        metadata = payload
    else:
        metadata = payload

    title = (
        metadata.get("title")
        or metadata.get("name")
        or metadata.get("eventType")
        or metadata.get("type")
        or source.external_id
    )
    return {
        "source_code": source.source_code,
        "upstream_id": source.external_id,
        "title": str(title)[:500],
        "source_url": _nasa_source_url(source.source_url),
        "retrieved_at": source.retrieved_at,
        "provenance": {
            "source": source.source_code,
            "upstream_id": source.external_id,
            "source_url": _nasa_source_url(source.source_url),
            "retrieved_at": source.retrieved_at,
        },
    }


def _saved_record_item(saved: SavedRecord, source: SourceRecord) -> dict[str, Any]:
    return {
        "id": str(saved.id),
        "created_at": saved.created_at,
        "record": _saved_record_summary(source),
    }


@router.get("/auth/me")
async def get_me(
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    account = await _account_for(session, user)
    return {
        "id": str(account.id),
        "subject": user.subject,
        "role": account.role,
        "created_at": account.created_at,
        "last_seen_at": account.last_seen_at,
        "is_development_identity": user.is_development_identity,
    }


@router.post("/saved-records", status_code=201)
async def save_record(
    body: SavedRecordCreate,
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    account = await _account_for(session, user)
    source_record = await session.scalar(
        select(SourceRecord).where(
            SourceRecord.source_code == body.source_code,
            SourceRecord.external_id == body.upstream_id,
        )
    )
    if source_record is None:
        raise AppError("not_found", "Not found", "The source record is not available to save.", 404)
    existing = await session.scalar(
        select(SavedRecord).where(
            SavedRecord.user_id == account.id,
            SavedRecord.source_record_id == source_record.id,
        )
    )
    if existing is not None:
        return _saved_record_item(existing, source_record)
    saved = SavedRecord(user_id=account.id, source_record_id=source_record.id)
    session.add(saved)
    await session.flush()
    return _saved_record_item(saved, source_record)


@router.get("/saved-records")
async def list_saved_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    account = await _account_for(session, user)
    total = int(
        await session.scalar(
            select(func.count()).select_from(SavedRecord).where(SavedRecord.user_id == account.id)
        )
        or 0
    )
    rows = (
        await session.execute(
            select(SavedRecord, SourceRecord)
            .join(SourceRecord, SavedRecord.source_record_id == SourceRecord.id)
            .where(SavedRecord.user_id == account.id)
            .order_by(SavedRecord.created_at.desc(), SavedRecord.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    now = datetime.now(UTC)
    return {
        "items": [_saved_record_item(saved, source) for saved, source in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
        "retrieved_at": now,
        "freshness": "current",
    }


@router.delete("/saved-records/{saved_id}", status_code=204)
async def delete_saved_record(
    saved_id: UUID,
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    account = await _account_for(session, user)
    saved = await session.scalar(
        select(SavedRecord).where(SavedRecord.id == saved_id, SavedRecord.user_id == account.id)
    )
    if saved is None:
        raise AppError("not_found", "Not found", "The saved record was not found.", 404)
    await session.delete(saved)
    return Response(status_code=204)


def _conversation_item(
    conversation: ResearchConversation, *, include_messages: bool
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": str(conversation.id),
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }
    if include_messages:
        item["messages"] = [
            {
                "id": str(message.id),
                "role": message.role,
                "content": message.content,
                "status": message.status,
                "created_at": message.created_at,
            }
            for message in conversation.messages
        ]
    return item


@router.post("/research/conversations", status_code=201)
async def create_conversation(
    body: ConversationCreate,
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    account = await _account_for(session, user)
    conversation = ResearchConversation(user_id=account.id, title=body.title)
    session.add(conversation)
    await session.flush()
    return _conversation_item(conversation, include_messages=False)


@router.get("/research/conversations")
async def list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    account = await _account_for(session, user)
    query = select(ResearchConversation).where(
        ResearchConversation.user_id == account.id,
        ResearchConversation.deleted_at.is_(None),
    )
    total = int(await session.scalar(select(func.count()).select_from(query.subquery())) or 0)
    conversations = (
        await session.scalars(
            query.order_by(ResearchConversation.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    now = datetime.now(UTC)
    return {
        "items": [_conversation_item(item, include_messages=False) for item in conversations],
        "page": page,
        "page_size": page_size,
        "total": total,
        "retrieved_at": now,
        "freshness": "current",
    }


async def _owned_conversation(
    session: AsyncSession,
    account: UserAccount,
    conversation_id: UUID,
    *,
    include_messages: bool = False,
) -> ResearchConversation:
    query = select(ResearchConversation).where(
        ResearchConversation.id == conversation_id,
        ResearchConversation.user_id == account.id,
        ResearchConversation.deleted_at.is_(None),
    )
    if include_messages:
        query = query.options(selectinload(ResearchConversation.messages))
    conversation = await session.scalar(query)
    if conversation is None:
        raise AppError("not_found", "Not found", "The conversation was not found.", 404)
    return conversation


@router.get("/research/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    account = await _account_for(session, user)
    conversation = await _owned_conversation(
        session, account, conversation_id, include_messages=True
    )
    return _conversation_item(conversation, include_messages=True)


@router.post("/research/conversations/{conversation_id}/messages", status_code=201)
async def submit_conversation_message(
    conversation_id: UUID,
    body: ConversationMessageCreate,
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    account = await _account_for(session, user)
    await _owned_conversation(session, account, conversation_id)
    await limiter.check(f"ai:{user.subject}", settings.ai_rate_limit_per_minute)
    if not settings.nasa_ai_policy_approved:
        raise FeatureUnavailableError(
            "assistant_policy_unavailable",
            "Research generation is disabled pending the required NASA policy review.",
        )
    # A provider adapter and evidence pipeline are required before generation can run.
    raise FeatureUnavailableError(
        "assistant_unavailable", "The research generation service is not configured."
    )


@router.delete("/research/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    account = await _account_for(session, user)
    conversation = await _owned_conversation(session, account, conversation_id)
    await session.delete(conversation)
    return Response(status_code=204)


@router.post("/reports", status_code=201)
async def create_report(
    body: ReportCreate,
    user: UserContext = Depends(require_user),
    settings: Settings = Depends(get_settings),
) -> None:
    await limiter.check(f"report:{user.subject}", settings.report_rate_limit_per_hour, 3600)
    code = (
        "assistant_policy_unavailable"
        if not settings.nasa_ai_policy_approved
        else "assistant_unavailable"
    )
    detail = (
        "Research generation is disabled pending the required NASA policy review."
        if not settings.nasa_ai_policy_approved
        else "The research generation service is not configured."
    )
    raise FeatureUnavailableError(code, detail)


def _report_item(report: AIReport) -> dict[str, Any]:
    return {
        "id": str(report.id),
        "title": report.title,
        "question": report.question,
        "structured_answer": report.structured_answer,
        "model_id": report.model_id,
        "generated_at": report.created_at,
        "citations": [
            {
                "citation_key": evidence.citation_key,
                "rank": evidence.rank,
                "source": evidence.source_record.source_code,
                "upstream_id": evidence.source_record.external_id,
                "source_url": _nasa_source_url(evidence.source_record.source_url),
                "retrieved_at": evidence.source_record.retrieved_at,
            }
            for evidence in report.evidence
        ],
    }


def _report_query(account: UserAccount) -> Select[AIReport]:
    return (
        select(AIReport)
        .where(AIReport.user_id == account.id, AIReport.deleted_at.is_(None))
        .options(selectinload(AIReport.evidence).selectinload(ReportEvidence.source_record))
    )


@router.get("/reports")
async def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    account = await _account_for(session, user)
    query = _report_query(account)
    total = int(await session.scalar(select(func.count()).select_from(query.subquery())) or 0)
    reports = (
        await session.scalars(
            query.order_by(AIReport.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    now = datetime.now(UTC)
    return {
        "items": [_report_item(report) for report in reports],
        "page": page,
        "page_size": page_size,
        "total": total,
        "retrieved_at": now,
        "freshness": "current",
    }


@router.get("/reports/{report_id}")
async def get_report(
    report_id: UUID,
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    account = await _account_for(session, user)
    report = await session.scalar(_report_query(account).where(AIReport.id == report_id))
    if report is None:
        raise AppError("not_found", "Not found", "The report was not found.", 404)
    return _report_item(report)


@router.delete("/reports/{report_id}", status_code=204)
async def delete_report(
    report_id: UUID,
    user: UserContext = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    account = await _account_for(session, user)
    report = await session.scalar(
        select(AIReport).where(
            AIReport.id == report_id,
            AIReport.user_id == account.id,
            AIReport.deleted_at.is_(None),
        )
    )
    if report is None:
        raise AppError("not_found", "Not found", "The report was not found.", 404)
    await session.delete(report)
    return Response(status_code=204)


@router.post("/asteroids/compare")
async def compare_asteroids(
    body: NeoComparisonRequest,
    user: UserContext = Depends(require_user),
    clients: NASAClients = Depends(get_nasa_clients),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    await _account_for(session, user)
    retrieved_at = datetime.now(UTC)
    objects = []
    for neo_id in body.neo_ids:
        record = await clients.neows.get(neo_id)
        raw = record.model_dump(mode="json")
        await persist_neo(session, raw, retrieved_at)
        diameter = record.estimated_diameter.get("kilometers", {})
        approaches = []
        for approach in record.close_approach_data:
            velocity = approach.relative_velocity.get("kilometers_per_second")
            miss_distance = approach.miss_distance.get("kilometers")
            try:
                velocity_value = float(velocity) if velocity is not None else None
            except (TypeError, ValueError):
                velocity_value = None
            try:
                distance_value = float(miss_distance) if miss_distance is not None else None
            except (TypeError, ValueError):
                distance_value = None
            approaches.append(
                {
                    "date": approach.close_approach_date.isoformat(),
                    "relative_velocity_km_s": velocity_value,
                    "miss_distance_km": distance_value,
                    "orbiting_body": approach.orbiting_body,
                }
            )
        objects.append(
            {
                "neo_id": record.id,
                "name": record.name,
                "absolute_magnitude": record.absolute_magnitude_h,
                "potentially_hazardous": record.is_potentially_hazardous_asteroid,
                "estimated_diameter_km": {
                    "min": diameter.get("estimated_diameter_min"),
                    "max": diameter.get("estimated_diameter_max"),
                },
                "close_approaches": approaches,
                "source_url": _nasa_source_url(
                    str(record.nasa_jpl_url) if record.nasa_jpl_url else None
                ),
                "retrieved_at": retrieved_at,
            }
        )
    return {
        "objects": objects,
        "units": {"diameter": "km", "relative_velocity": "km/s", "miss_distance": "km"},
        "disclaimer": "Source measurements are descriptive and are not an impact prediction.",
        "retrieved_at": retrieved_at,
    }


@admin_router.get("/sources")
async def admin_sources(
    _admin: UserContext = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    latest = (
        select(SourceRecord.source_code, func.max(SourceRecord.retrieved_at).label("retrieved_at"))
        .group_by(SourceRecord.source_code)
        .subquery()
    )
    rows = (
        await session.execute(
            select(DataSource, latest.c.retrieved_at)
            .outerjoin(latest, latest.c.source_code == DataSource.code)
            .order_by(DataSource.code)
        )
    ).all()
    items = []
    for row in rows:
        source = cast(DataSource, row[0])
        retrieved_at = cast(datetime | None, row[1])
        items.append(
            {
                "source_code": source.code,
                "display_name": source.display_name,
                "base_host": source.base_host,
                "enabled": source.enabled,
                "last_retrieved_at": retrieved_at,
            }
        )
    return {"items": items}


@admin_router.get("/jobs")
async def admin_jobs(
    state: Literal["queued", "running", "succeeded", "failed"] | None = None,
    source_code: str | None = Query(default=None, min_length=2, max_length=40),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: UserContext = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    query = select(IngestionJob)
    count_query = select(func.count()).select_from(IngestionJob)
    if state:
        query = query.where(IngestionJob.state == state)
        count_query = count_query.where(IngestionJob.state == state)
    if source_code:
        query = query.where(IngestionJob.source_code == source_code)
        count_query = count_query.where(IngestionJob.source_code == source_code)
    total = int(await session.scalar(count_query) or 0)
    jobs = (
        await session.scalars(
            query.order_by(IngestionJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "items": [
            {
                "id": str(job.id),
                "source_code": job.source_code,
                "job_type": job.job_type,
                "state": job.state,
                "attempts": job.attempts,
                "next_run_at": job.next_run_at,
                "finished_at": job.finished_at,
                "counts": job.counts,
                "safe_error_code": job.safe_error_code,
                "created_at": job.created_at,
            }
            for job in jobs
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@admin_router.post("/jobs/{job_id}/retry", status_code=202)
async def retry_job(
    job_id: UUID,
    request: Request,
    admin: UserContext = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    job = await session.scalar(
        select(IngestionJob).where(IngestionJob.id == job_id).with_for_update()
    )
    if job is None or job.state != "failed":
        raise AppError(
            "retry_unavailable",
            "Retry unavailable",
            "The requested failed job is not eligible for retry.",
            409,
        )
    job.state = "queued"
    job.attempts = 0
    job.next_run_at = datetime.now(UTC)
    job.lease_until = None
    job.locked_by = None
    job.finished_at = None
    job.safe_error_code = None
    session.add(
        AuditEvent(
            actor_subject=admin.subject,
            action="ingestion_job.retry",
            target_type="ingestion_job",
            target_id=str(job.id),
            request_id=getattr(request.state, "request_id", None),
            details={"source_code": job.source_code, "job_type": job.job_type},
        )
    )
    await session.flush()
    return {"id": str(job.id), "state": job.state, "next_run_at": job.next_run_at}


__all__ = ["admin_router", "router"]
