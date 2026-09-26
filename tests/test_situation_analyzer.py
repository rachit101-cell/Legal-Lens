"""
LegalLens — Unit Tests for SituationAnalyzer and Deterministic Intelligence Pipeline.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.analysis import Clause as DBClause
from app.models.document import Document as DBDocument
from app.services.analysis.situation_analyzer import SituationAnalyzer
from packages.schemas.enums import DocumentType, TimelineEventType


@pytest.fixture
def mock_clauses() -> list[DBClause]:
    c1 = DBClause()
    c1.id = "cl-1"
    c1.document_id = "doc-test-123"
    c1.number = "1"
    c1.heading = "Notice of Default"
    c1.page_start = 1
    c1.page_end = 1
    c1.clause_type = "PAYMENT_FEES"
    c1.original_text = (
        "NOTICE TO CURE DEFAULT\n"
        "DATE: September 15, 2026\n"
        "TO: Alex Mercer (Tenant), Apt 4B\n"
        "FROM: Vanguard Properties LLC (Landlord)\n"
        "TAKE NOTICE that you are in default of Section 4 of the unsupplied Residential Lease Agreement.\n"
        "You owe overdue rent in the amount of $2,500.00."
    )
    c1.normalized_text = c1.original_text

    c2 = DBClause()
    c2.id = "cl-2"
    c2.document_id = "doc-test-123"
    c2.number = "2"
    c2.heading = "Demand for Compliance"
    c2.page_start = 2
    c2.page_end = 2
    c2.clause_type = "TERMINATION_NOTICE"
    c2.original_text = (
        "DEMAND FOR COMPLIANCE\n"
        "You must cure the aforementioned default within 15 days of service of this notice.\n"
        "Payment must be remitted via cashier's check or certified wire transfer."
    )
    c2.normalized_text = c2.original_text

    c3 = DBClause()
    c3.id = "cl-3"
    c3.document_id = "doc-test-123"
    c3.number = "3"
    c3.heading = "Termination Provision"
    c3.page_start = 3
    c3.page_end = 3
    c3.clause_type = "TERMINATION_NOTICE"
    c3.original_text = (
        "TERMINATION PROVISION\n"
        "If default is not cured, Landlord provides a 30-day notice of termination of tenancy.\n"
        "You will be required to vacate the premises on or before October 31, 2026.\n"
        "Signed: Vanguard Properties LLC"
    )
    c3.normalized_text = c3.original_text

    return [c1, c2, c3]


@pytest.fixture
def mock_document() -> DBDocument:
    doc = DBDocument()
    doc.id = "doc-test-123"
    doc.filename = "Tenant_Notice_To_Cure.pdf"
    doc.page_count = 3
    doc.language = "en"
    return doc


@pytest.mark.asyncio
async def test_situation_analyzer_full_pipeline(mock_document: DBDocument, mock_clauses: list[DBClause]):
    analyzer = SituationAnalyzer()

    # Mock database session
    mock_session = AsyncMock()
    mock_session.get.return_value = mock_document

    mock_exec_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_clauses
    mock_exec_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_exec_result

    result = await analyzer.analyze_document("doc-test-123", mock_session)

    # 1. Document Type & Parties
    assert result.overview.document_type == DocumentType.LEGAL_NOTICE
    party_names = [p["name"] if isinstance(p, dict) else str(p) for p in result.overview.parties]
    assert any("Alex Mercer" in name for name in party_names)
    assert any("Vanguard Properties" in name for name in party_names)

    # 2. Key Findings & Detectors
    categories = [f.category.value if hasattr(f.category, "value") else str(f.category) for f in result.findings]
    assert any("DEADLINE" in c for c in categories)
    assert any("TERMINATION" in c for c in categories)
    assert any("FINANCIAL" in c for c in categories)

    # 3. Timeline Events
    assert len(result.timeline) >= 2
    event_types = [e.event_type for e in result.timeline]
    assert TimelineEventType.RESPONSE_DEADLINE in event_types or TimelineEventType.DEADLINE in event_types

    # 4. Preparation Checklist & Questions
    assert len(result.checklist) >= 3
    assert len(result.lawyer_questions) >= 2


@pytest.mark.asyncio
async def test_situation_analyzer_caching(mock_document: DBDocument, mock_clauses: list[DBClause]):
    analyzer = SituationAnalyzer()

    mock_session = AsyncMock()
    mock_session.get.return_value = mock_document
    mock_exec_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_clauses
    mock_exec_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_exec_result

    # First call - populates cache
    res1 = await analyzer.analyze_document("doc-test-123", mock_session)
    assert res1 is not None

    # Second call - served from cache in sub-millisecond time
    start = time.perf_counter()
    res2 = await analyzer.analyze_document("doc-test-123", mock_session)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert res2 == res1
    assert elapsed_ms < 10.0  # In-memory retrieval < 10ms
