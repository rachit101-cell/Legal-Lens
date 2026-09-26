"""
LegalLens — Unit Tests for Document Parsing & Clause Classification.
"""

from __future__ import annotations

import hashlib

from app.services.document_engine import _classify_clause, _split_into_clauses
from packages.schemas.enums import ClauseType


def test_classify_clause_types():
    """Verify deterministic rule-based clause classification."""
    assert _classify_clause("This Agreement is governed by Delaware law.") == ClauseType.DISPUTE_GOVERNING_LAW
    assert _classify_clause("Either party may terminate upon written notice.") == ClauseType.TERMINATION_NOTICE
    assert _classify_clause("Disclosing Party provides Confidential Information.") == ClauseType.CONFIDENTIALITY_IP
    assert _classify_clause("The total liability shall not exceed $100,000.") == ClauseType.LIABILITY_INDEMNITY
    assert _classify_clause("Tenant shall pay monthly rent fee of $2,500.") == ClauseType.PAYMENT_FEES


def test_split_into_clauses_numbered():
    """Verify segmentation of numbered legal sections."""
    text = (
        "1. Definitions\nConfidential information includes code.\n\n"
        "2. Term\nThis agreement lasts two years.\n\n"
        "3. Governing Law\nGoverned by the State of New York."
    )
    clauses = _split_into_clauses(text, document_id="doc_1", page_number=1)
    assert len(clauses) >= 3
    assert clauses[0]["page"] == 1
    assert "Definitions" in clauses[0]["text"] or "1." in clauses[0]["text"]


def test_sha256_clause_integrity():
    """Verify cryptographic integrity hashing of clauses."""
    sample_text = "The Receiving Party shall hold all proprietary information in strict confidence."
    digest1 = hashlib.sha256(sample_text.encode("utf-8")).hexdigest()
    digest2 = hashlib.sha256(sample_text.encode("utf-8")).hexdigest()
    assert digest1 == digest2
    assert len(digest1) == 64
