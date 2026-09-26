"""
LegalLens — Unit Tests for Schemas and Invariants.
"""

from __future__ import annotations

from packages.schemas.domain import (
    Clause,
    UploadResponse,
)
from packages.schemas.enums import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    ClauseType,
    DocumentStatus,
    Severity,
    SupportStatus,
)


def test_enums_integrity():
    """Verify enum values and security-allowed MIME types and extensions."""
    assert ".pdf" in ALLOWED_EXTENSIONS
    assert ".docx" in ALLOWED_EXTENSIONS
    assert ".exe" not in ALLOWED_EXTENSIONS
    assert "application/pdf" in ALLOWED_MIME_TYPES
    assert "application/x-sh" not in ALLOWED_MIME_TYPES

    assert DocumentStatus.COMPLETED == "COMPLETED"
    assert Severity.IMPORTANT == "IMPORTANT"
    assert SupportStatus.SUPPORTED == "SUPPORTED"
    assert ClauseType.LIABILITY_INDEMNITY == "LIABILITY_INDEMNITY"


def test_upload_response_model():
    """Validate UploadResponse serialization and fields."""
    resp = UploadResponse(
        request_id="req_123",
        document_id="doc_456",
        analysis_id="an_789",
        status=DocumentStatus.QUEUED,
    )
    data = resp.model_dump()
    assert data["request_id"] == "req_123"
    assert data["document_id"] == "doc_456"
    assert data["status"] == "QUEUED"


def test_clause_model():
    """Validate Clause model with page coordinates and classification."""
    clause = Clause(
        clause_id="c_1",
        clause_type=ClauseType.TERMINATION_NOTICE,
        page_start=2,
        page_end=2,
        number="12.1",
        original_text="Either party may terminate upon 30 days notice.",
        normalized_text="either party may terminate upon 30 days notice.",
    )
    assert clause.page_start == 2
    assert clause.clause_type == ClauseType.TERMINATION_NOTICE
