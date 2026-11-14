"""User-owned records, conversations, generated reports, and audit metadata."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import JSON_DOCUMENT

if TYPE_CHECKING:
    from app.db.models.sources import SourceRecord


class UserAccount(Base):
    """Minimal local identity mapping keyed by validated OIDC subject."""

    __tablename__ = "user_account"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    oidc_subject: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(
        String(40), nullable=False, default="user", server_default="user"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    saved_records: Mapped[list["SavedRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["ResearchConversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reports: Mapped[list["AIReport"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class SavedRecord(Base):
    """User-owned link to a canonical source record."""

    __tablename__ = "saved_record"
    __table_args__ = (
        UniqueConstraint("user_id", "source_record_id", name="uq_saved_record_user_source"),
        Index("ix_saved_record_user_created", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False
    )
    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_record.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[UserAccount] = relationship(back_populates="saved_records")
    source_record: Mapped["SourceRecord"] = relationship()


class ResearchConversation(Base):
    """Owner-scoped research conversation."""

    __tablename__ = "research_conversation"
    __table_args__ = (Index("ix_research_conversation_user_updated", "user_id", "updated_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[UserAccount] = relationship(back_populates="conversations")
    messages: Mapped[list["ResearchMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ResearchMessage.created_at",
    )


class ResearchMessage(Base):
    """A user or assistant message with generation metadata where applicable."""

    __tablename__ = "research_message"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="role_allowed"),
        Index("ix_research_message_conversation_created", "conversation_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_conversation.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    prompt_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("prompt_version.id", ondelete="SET NULL")
    )
    model_id: Mapped[str | None] = mapped_column(String(255))
    usage: Mapped[dict[str, Any] | None] = mapped_column(JSON_DOCUMENT)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="complete", server_default="complete"
    )

    conversation: Mapped[ResearchConversation] = relationship(back_populates="messages")


class PromptVersion(Base):
    """Reviewed and checksummed prompt template version."""

    __tablename__ = "prompt_version"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_prompt_version_name_version"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    system_template: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")


class AIReport(Base):
    """Owner-scoped report with its generated output and model provenance."""

    __tablename__ = "ai_report"
    __table_args__ = (Index("ix_ai_report_user_created", "user_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False
    )
    prompt_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("prompt_version.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    structured_answer: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[UserAccount] = relationship(back_populates="reports")
    prompt_version: Mapped[PromptVersion] = relationship()
    evidence: Mapped[list["ReportEvidence"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class ReportEvidence(Base):
    """Exact source-record references used to support a generated report."""

    __tablename__ = "report_evidence"
    __table_args__ = (
        UniqueConstraint("report_id", "citation_key", name="uq_report_evidence_citation"),
        Index("ix_report_evidence_source", "source_record_id"),
    )

    report_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_report.id", ondelete="CASCADE"), primary_key=True
    )
    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_record.id", ondelete="RESTRICT"), primary_key=True
    )
    citation_key: Mapped[str] = mapped_column(String(80), nullable=False)
    excerpt_hash: Mapped[str | None] = mapped_column(String(64))
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    report: Mapped[AIReport] = relationship(back_populates="evidence")
    source_record: Mapped["SourceRecord"] = relationship()


class AuditEvent(Base):
    """Metadata-only security and administrative audit event."""

    __tablename__ = "audit_event"
    __table_args__ = (Index("ix_audit_event_created", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_subject: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(255))
    request_id: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
