"""
LegalLens — Shared Enums.

All status types, source types, severity levels, and classification
enums used across the API, analysis engine, and frontend.
"""

from __future__ import annotations

from enum import StrEnum


# ── Document Statuses ────────────────────────────────────────────


class DocumentStatus(StrEnum):
    """Processing lifecycle of a document."""

    UPLOADING = "UPLOADING"
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    EXTRACTING = "EXTRACTING"
    ANALYZING = "ANALYZING"
    INDEXING = "INDEXING"
    GENERATING = "GENERATING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    DELETED = "DELETED"


class AnalysisStatus(StrEnum):
    """Status of an analysis run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class AnalysisStage(StrEnum):
    """Named processing stages shown to the user."""

    VALIDATING_FILE = "VALIDATING_FILE"
    EXTRACTING_PAGES = "EXTRACTING_PAGES"
    IDENTIFYING_CLAUSES = "IDENTIFYING_CLAUSES"
    CHECKING_DATES_AMOUNTS = "CHECKING_DATES_AMOUNTS"
    BUILDING_EVIDENCE = "BUILDING_EVIDENCE"
    GENERATING_EXPLANATIONS = "GENERATING_EXPLANATIONS"
    VERIFYING_CITATIONS = "VERIFYING_CITATIONS"


# ── Text Source ──────────────────────────────────────────────────


class TextSource(StrEnum):
    """How text was obtained from a page."""

    NATIVE_TEXT = "NATIVE_TEXT"
    OCR = "OCR"
    MIXED = "MIXED"


# ── Document Types ───────────────────────────────────────────────


class DocumentType(StrEnum):
    """Broad document classification."""

    LEGAL_NOTICE = "LEGAL_NOTICE"
    LEASE_AGREEMENT = "LEASE_AGREEMENT"
    EMPLOYMENT_AGREEMENT = "EMPLOYMENT_AGREEMENT"
    SERVICE_AGREEMENT = "SERVICE_AGREEMENT"
    NON_DISCLOSURE_AGREEMENT = "NON_DISCLOSURE_AGREEMENT"
    PURCHASE_AGREEMENT = "PURCHASE_AGREEMENT"
    POWER_OF_ATTORNEY = "POWER_OF_ATTORNEY"
    COURT_ORDER = "COURT_ORDER"
    INVOICE = "INVOICE"
    OTHER = "OTHER"


# ── Clause Taxonomy ──────────────────────────────────────────────


class ClauseType(StrEnum):
    """Clause taxonomy categories."""

    PAYMENT_FEES = "PAYMENT_FEES"
    TERM_RENEWAL = "TERM_RENEWAL"
    TERMINATION_NOTICE = "TERMINATION_NOTICE"
    LIABILITY_INDEMNITY = "LIABILITY_INDEMNITY"
    CONFIDENTIALITY_IP = "CONFIDENTIALITY_IP"
    NON_COMPETE_NON_SOLICIT = "NON_COMPETE_NON_SOLICIT"
    DISPUTE_GOVERNING_LAW = "DISPUTE_GOVERNING_LAW"
    PRIVACY_DATA = "PRIVACY_DATA"
    BOILERPLATE = "BOILERPLATE"
    MISCELLANEOUS = "MISCELLANEOUS"
    OTHER = "OTHER"


# ── Entity Types ─────────────────────────────────────────────────


class EntityType(StrEnum):
    """Types of entities extracted from documents."""

    DATE = "DATE"
    MONEY = "MONEY"
    PERCENTAGE = "PERCENTAGE"
    DURATION = "DURATION"
    NOTICE_PERIOD = "NOTICE_PERIOD"
    CLAUSE_NUMBER = "CLAUSE_NUMBER"
    STATUTE_REFERENCE = "STATUTE_REFERENCE"
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    ADDRESS = "ADDRESS"


class ExtractionMethod(StrEnum):
    """How an entity was extracted."""

    REGEX = "REGEX"
    NER = "NER"
    RULE = "RULE"
    LLM = "LLM"


# ── Finding Severity ─────────────────────────────────────────────


class Severity(StrEnum):
    """Transparent severity labels — NOT numeric risk scores."""

    IMPORTANT = "IMPORTANT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    ATTENTION_REQUIRED = "ATTENTION_REQUIRED"
    INFORMATION_MISSING = "INFORMATION_MISSING"


class FindingCategory(StrEnum):
    """Categories of attention findings."""

    FINANCIAL = "FINANCIAL"
    COMMITMENT = "COMMITMENT"
    LIABILITY = "LIABILITY"
    TERMINATION = "TERMINATION"
    CONSISTENCY = "CONSISTENCY"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    DEADLINE = "DEADLINE"
    OTHER = "OTHER"


# ── Evidence & Citation ──────────────────────────────────────────


class VerificationStatus(StrEnum):
    """Status of evidence verification."""

    VERIFIED = "VERIFIED"
    OCR_APPROXIMATE = "OCR_APPROXIMATE"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class SupportStatus(StrEnum):
    """How well evidence supports a claim."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNVERIFIED = "UNVERIFIED"


class SourceType(StrEnum):
    """Source of information."""

    USER_DOCUMENT = "USER_DOCUMENT"
    AI_GENERATED = "AI_GENERATED"
    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"


# ── Timeline ─────────────────────────────────────────────────────


class DateStatus(StrEnum):
    """How a date was determined."""

    EXPLICIT = "EXPLICIT"
    EXTRACTED = "EXTRACTED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"


class TimelineEventType(StrEnum):
    """Types of timeline events."""

    START_DATE = "START_DATE"
    END_DATE = "END_DATE"
    DEADLINE = "DEADLINE"
    NOTICE_PERIOD = "NOTICE_PERIOD"
    PAYMENT_DUE = "PAYMENT_DUE"
    RENEWAL_WINDOW = "RENEWAL_WINDOW"
    TERMINATION_WINDOW = "TERMINATION_WINDOW"
    RESPONSE_DEADLINE = "RESPONSE_DEADLINE"
    OTHER = "OTHER"


# ── Chat ─────────────────────────────────────────────────────────


class AnswerStatus(StrEnum):
    """Status of a chat answer."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNVERIFIED = "UNVERIFIED"


class MessageRole(StrEnum):
    """Chat message roles."""

    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


# ── Checklist ────────────────────────────────────────────────────


class ChecklistStatus(StrEnum):
    """Status of a checklist item."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# ── Audit ────────────────────────────────────────────────────────


class AuditEventType(StrEnum):
    """Types of audit events."""

    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_ANALYZED = "DOCUMENT_ANALYZED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    DOCUMENT_ACCESSED = "DOCUMENT_ACCESSED"
    CHAT_QUESTION = "CHAT_QUESTION"
    CHAT_ANSWER = "CHAT_ANSWER"
    ANALYSIS_STARTED = "ANALYSIS_STARTED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    CITATION_REJECTED = "CITATION_REJECTED"
    PROMPT_INJECTION_SUSPECTED = "PROMPT_INJECTION_SUSPECTED"
    RATE_LIMIT_HIT = "RATE_LIMIT_HIT"
    AUTH_FAILURE = "AUTH_FAILURE"


# ── MIME Types ───────────────────────────────────────────────────

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

MIME_TO_EXTENSION = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
