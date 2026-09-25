"""
LegalLens — Domain Schemas.

Canonical Pydantic models shared between the API, analysis engine,
and frontend. These are the boundary contracts — all components
import these types rather than ad hoc dictionaries.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from packages.schemas.enums import (
    AnalysisStage,
    AnalysisStatus,
    AnswerStatus,
    ChecklistStatus,
    ClauseType,
    DateStatus,
    DocumentStatus,
    DocumentType,
    EntityType,
    ExtractionMethod,
    FindingCategory,
    MessageRole,
    Severity,
    SourceType,
    SupportStatus,
    TextSource,
    TimelineEventType,
    VerificationStatus,
)


# ── Base Models ──────────────────────────────────────────────────


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


# ── Document Schemas ─────────────────────────────────────────────


class TextBlock(BaseModel):
    """A text block within a page with spatial coordinates."""

    block_id: str
    text: str
    bbox: list[float] | None = None  # [x0, y0, x1, y1]
    order: int


class CanonicalPage(BaseModel):
    """Parser-independent page representation."""

    page_id: str
    page_number: int
    text: str
    text_source: TextSource
    ocr_quality: float | None = None
    width: float | None = None
    height: float | None = None
    blocks: list[TextBlock] = Field(default_factory=list)
    content_hash: str


class Section(BaseModel):
    """A document section (heading level)."""

    section_id: str
    number: str | None = None
    heading: str | None = None
    page_start: int
    page_end: int
    parent_section_id: str | None = None


class Clause(BaseModel):
    """A legal clause within a section."""

    clause_id: str
    section_id: str | None = None
    number: str | None = None
    heading: str | None = None
    original_text: str
    normalized_text: str
    page_start: int
    page_end: int
    bbox: list[float] | None = None
    char_start: int | None = None
    char_end: int | None = None
    source_block_ids: list[str] = Field(default_factory=list)
    clause_type: ClauseType = ClauseType.OTHER
    classification_confidence: float | None = None


class Entity(BaseModel):
    """An extracted entity (date, money, party, etc.)."""

    entity_id: str
    entity_type: EntityType
    surface_form: str
    normalized_value: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    page_number: int
    clause_id: str | None = None
    char_start: int | None = None
    char_end: int | None = None
    extraction_method: ExtractionMethod


class DocumentMetadata(BaseModel):
    """Extraction metadata."""

    extraction_version: str = "1.0.0"
    parser: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CanonicalDocument(BaseModel):
    """Complete canonical document representation."""

    document_id: str
    document_type: DocumentType = DocumentType.OTHER
    language: str = "en"
    source_filename: str
    page_count: int
    pages: list[CanonicalPage] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    clauses: list[Clause] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    metadata: DocumentMetadata


# ── Evidence & Citation Schemas ──────────────────────────────────


class Evidence(BaseModel):
    """A piece of evidence from the source document."""

    evidence_id: str
    document_id: str
    page_number: int
    section_id: str | None = None
    clause_id: str | None = None
    quote: str
    quote_hash: str
    char_start: int | None = None
    char_end: int | None = None
    bbox: list[float] | None = None
    source_type: SourceType = SourceType.USER_DOCUMENT
    verification_status: VerificationStatus = VerificationStatus.PENDING


class Claim(BaseModel):
    """A claim with supporting evidence and verification status."""

    claim_id: str
    claim: str
    supporting_evidence: list[str] = Field(default_factory=list)  # evidence IDs
    support_status: SupportStatus
    verification_notes: str | None = None


# ── Finding Schemas ──────────────────────────────────────────────


class Finding(BaseModel):
    """An attention finding with transparent categorization."""

    finding_id: str
    category: FindingCategory
    severity: Severity
    title: str
    explanation: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = True
    detector_version: str
    why_shown: str | None = None
    cannot_determine: str | None = None


# ── Timeline Schemas ─────────────────────────────────────────────


class TimelineEvent(BaseModel):
    """A timeline event with date status classification."""

    event_id: str
    event_type: TimelineEventType
    label: str
    date_value: str | None = None  # ISO format date string
    duration_days: int | None = None
    date_status: DateStatus
    calculation_trace: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


# ── Checklist & Questions ────────────────────────────────────────


class ChecklistItem(BaseModel):
    """A preparation checklist item."""

    item_id: str
    text: str
    status: ChecklistStatus = ChecklistStatus.PENDING
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)
    sort_order: int = 0


class LawyerQuestion(BaseModel):
    """A question to ask a legal professional."""

    question_id: str
    question: str
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)
    sort_order: int = 0


# ── Analysis Schemas ─────────────────────────────────────────────


class AnalysisStageStatus(BaseModel):
    """Status of a single processing stage."""

    stage: AnalysisStage
    status: str  # "pending", "running", "completed", "failed"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    elapsed_ms: int | None = None
    error: str | None = None


class AnalysisOverview(BaseModel):
    """Document overview in the Legal Situation Map."""

    document_type: DocumentType
    document_type_label: str
    language: str
    page_count: int
    parties: list[dict[str, str]] = Field(default_factory=list)
    key_dates: list[dict[str, str]] = Field(default_factory=list)
    situation_snapshot: str | None = None


class AnalysisResult(BaseModel):
    """Complete analysis result — the Legal Situation Map."""

    analysis_id: str
    document_id: str
    version: int = 1
    status: AnalysisStatus
    stages: list[AnalysisStageStatus] = Field(default_factory=list)
    overview: AnalysisOverview | None = None
    clauses: list[Clause] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    lawyer_questions: list[LawyerQuestion] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    disclaimers: list[str] = Field(
        default_factory=lambda: [
            "This analysis is based on the supplied document and sources.",
            "AI can make mistakes.",
            "Decisions requiring professional judgment should be reviewed with a qualified legal professional.",
        ]
    )
    prompt_version: str | None = None
    model: str | None = None
    total_duration_ms: int | None = None


# ── Chat Schemas ─────────────────────────────────────────────────


class ChatCitation(BaseModel):
    """A citation in a chat answer."""

    evidence_id: str
    page_number: int
    clause_id: str | None = None
    quote: str


class ChatMessage(BaseModel):
    """A chat message (question or answer)."""

    message_id: str
    session_id: str
    role: MessageRole
    content: str
    answer_status: AnswerStatus | None = None
    citations: list[ChatCitation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── API Response Schemas ─────────────────────────────────────────


class APIError(BaseModel):
    """Structured error response."""

    code: str
    message: str


class APIResponse(BaseModel):
    """Standard API response envelope."""

    request_id: str
    data: dict | list | None = None
    error: APIError | None = None


class UploadResponse(BaseModel):
    """Response from document upload."""

    request_id: str
    document_id: str
    analysis_id: str
    status: DocumentStatus


class ChatMessageRequest(BaseModel):
    """Request to send a chat message."""
    message: str


class Citation(BaseModel):
    """A citation generated by the AI model."""
    claim: str
    source_ids: list[str] = Field(default_factory=list)


class ChatMessageResponse(BaseModel):
    """Response from the AI model generation pipeline."""
    answer: str
    answer_status: AnswerStatus
    citations: list[Citation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class DocumentResponse(BaseModel):
    """Response for document metadata."""

    request_id: str
    document_id: str
    filename: str
    mime_type: str
    page_count: int | None = None
    status: DocumentStatus
    language: str | None = None
    document_type: DocumentType | None = None
    created_at: datetime
    expires_at: datetime | None = None


class ChatResponse(BaseModel):
    """Response from chat Q&A."""

    request_id: str
    message_id: str
    answer: str
    answer_status: AnswerStatus
    citations: list[ChatCitation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str
    request_id: str
    environment: str | None = None
