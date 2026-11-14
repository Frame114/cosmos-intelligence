"""Metadata-level checks for the SQLAlchemy persistence model."""

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql

from app.db import Base
from app.db.models.types import JSON_DOCUMENT


def test_required_domain_and_user_tables_are_registered() -> None:
    expected = {
        "data_source",
        "source_record",
        "apod_record",
        "neo_object",
        "neo_approach",
        "space_weather_event",
        "earth_event",
        "media_record",
        "ingestion_job",
        "api_request_log",
        "audit_event",
        "user_account",
        "saved_record",
        "research_conversation",
        "research_message",
        "prompt_version",
        "ai_report",
        "report_evidence",
    }

    assert expected <= Base.metadata.tables.keys()


def test_source_identity_and_saved_record_are_unique() -> None:
    source_constraints = Base.metadata.tables["source_record"].constraints
    saved_constraints = Base.metadata.tables["saved_record"].constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns} == {"source_code", "external_id"}
        for constraint in source_constraints
    )
    assert any(
        isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns} == {"user_id", "source_record_id"}
        for constraint in saved_constraints
    )


def test_domain_and_job_guards_are_present() -> None:
    apod_constraints = Base.metadata.tables["apod_record"].constraints
    job_constraints = Base.metadata.tables["ingestion_job"].constraints

    assert any(isinstance(constraint, CheckConstraint) for constraint in apod_constraints)
    assert any(isinstance(constraint, CheckConstraint) for constraint in job_constraints)


def test_json_document_uses_postgresql_jsonb_variant() -> None:
    assert isinstance(JSON_DOCUMENT.dialect_impl(postgresql.dialect()), postgresql.JSONB)
