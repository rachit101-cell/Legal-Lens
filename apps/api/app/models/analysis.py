"""
LegalLens API — Analysis SQLAlchemy Models.

Models for clauses, entities, findings, timeline, and checklist items.
"""

from __future__ import annotations

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Float, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_prefixed_uuid
from packages.schemas.enums import (
    AnalysisStatus,
    ChecklistStatus,
    ClauseType,
    DateStatus,
    EntityType,
    ExtractionMethod,
    FindingCategory,
    Severity,
    TimelineEventType,
)


class AnalysisRun(Base, TimestampMixin):
    """A run of the analysis pipeline."""

    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("run"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[int] = mapped_column(BigInteger, default=1)

    status: Mapped[str] = mapped_column(
        ENUM(AnalysisStatus, name="analysis_status_enum", create_type=False),
        nullable=False,
        default=AnalysisStatus.QUEUED,
        index=True,
    )

    stages: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    overview: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    total_duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class Clause(Base, TimestampMixin):
    """A legal clause within a document."""

    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("cl"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    section_id: Mapped[str | None] = mapped_column(String, nullable=True)

    number: Mapped[str | None] = mapped_column(String, nullable=True)
    heading: Mapped[str | None] = mapped_column(String, nullable=True)

    original_text: Mapped[str] = mapped_column(String)
    normalized_text: Mapped[str] = mapped_column(String)

    page_start: Mapped[int] = mapped_column(BigInteger)
    page_end: Mapped[int] = mapped_column(BigInteger)
    bbox: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)
    char_start: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    char_end: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    source_block_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)

    clause_type: Mapped[str] = mapped_column(
        ENUM(ClauseType, name="clause_type_enum", create_type=False),
        default=ClauseType.OTHER,
    )
    classification_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Vector embedding for retrieval
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)


class Entity(Base, TimestampMixin):
    """An extracted entity (date, money, party, etc.)."""

    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("ent"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    clause_id: Mapped[str | None] = mapped_column(String, nullable=True)

    entity_type: Mapped[str] = mapped_column(
        ENUM(EntityType, name="entity_type_enum", create_type=False),
        nullable=False,
    )

    surface_form: Mapped[str] = mapped_column(String)
    normalized_value: Mapped[str | None] = mapped_column(String, nullable=True)

    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    page_number: Mapped[int] = mapped_column(BigInteger)
    char_start: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    char_end: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    extraction_method: Mapped[str] = mapped_column(
        ENUM(ExtractionMethod, name="extraction_method_enum", create_type=False),
        nullable=False,
    )


class Finding(Base, TimestampMixin):
    """An attention finding with transparent categorization."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("fnd"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    analysis_id: Mapped[str] = mapped_column(String, index=True)

    category: Mapped[str] = mapped_column(
        ENUM(FindingCategory, name="finding_category_enum", create_type=False),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        ENUM(Severity, name="severity_enum", create_type=False),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String)
    explanation: Mapped[str] = mapped_column(String)

    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    requires_human_review: Mapped[bool] = mapped_column(default=True)

    detector_version: Mapped[str] = mapped_column(String)
    why_shown: Mapped[str | None] = mapped_column(String, nullable=True)
    cannot_determine: Mapped[str | None] = mapped_column(String, nullable=True)


class TimelineEvent(Base, TimestampMixin):
    """A timeline event with date status classification."""

    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("evt"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    analysis_id: Mapped[str] = mapped_column(String, index=True)

    event_type: Mapped[str] = mapped_column(
        ENUM(TimelineEventType, name="timeline_event_type_enum", create_type=False),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(String)
    date_value: Mapped[str | None] = mapped_column(String, nullable=True)
    duration_days: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    date_status: Mapped[str] = mapped_column(
        ENUM(DateStatus, name="date_status_enum", create_type=False),
        nullable=False,
    )

    calculation_trace: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)


class ChecklistItem(Base, TimestampMixin):
    """A preparation checklist item."""

    __tablename__ = "checklist_items"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("chk"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    analysis_id: Mapped[str] = mapped_column(String, index=True)

    text: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(
        ENUM(ChecklistStatus, name="checklist_status_enum", create_type=False),
        default=ChecklistStatus.PENDING,
    )
    reason: Mapped[str] = mapped_column(String)
    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)
