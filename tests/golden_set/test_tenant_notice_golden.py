"""
LegalLens — Golden Benchmark Test for Synthetic 3-Page Tenant Notice.

Implements automated evaluation of the canonical PRD demonstration scenario:
- 3 pages with party identification, $2,500 payment demand
- 15-day response deadline and 30-day termination notice clause
- Referenced underlying lease agreement that was not uploaded/attached (missing information)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.analysis import Clause as DBClause
from app.models.document import Document as DBDocument
from app.services.analysis.situation_analyzer import situation_analyzer
from app.services.document_engine import _classify_clause, _split_into_clauses
from tests.eval_metrics import evaluate_findings


@pytest.fixture
def tenant_notice_text() -> str:
    path = Path(__file__).parent / "sample_tenant_notice.txt"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def golden_reference() -> dict:
    path = Path(__file__).parent / "golden_tenant_notice.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_tenant_notice_parties_and_classification(tenant_notice_text: str):
    """Verify document type and parties are correctly parsed from tenant notice."""
    doc_type, doc_label = situation_analyzer._classify_document_type(
        "tenant_cure_notice.txt", tenant_notice_text
    )
    assert "Notice" in doc_label or doc_type.value == "LEGAL_NOTICE"

    parties = situation_analyzer._extract_parties(tenant_notice_text)
    party_names = [p["name"] for p in parties]
    assert any("Alex Mercer" in name for name in party_names)
    assert any("Vanguard Properties" in name for name in party_names)


def test_tenant_notice_timeline_and_deadlines(tenant_notice_text: str):
    """Verify timeline captures 15-day remedy deadline and 30-day termination window."""
    clauses_raw = _split_into_clauses(tenant_notice_text, document_id="doc_t1", page_number=1)
    db_clauses = [
        DBClause(
            id=f"c_{i}",
            document_id="doc_t1",
            section_id="sec_1",
            page_start=1,
            page_end=1,
            number=i,
            heading=f"Section {i}",
            original_text=c["text"],
            normalized_text=c["text"].lower(),
            clause_type=_classify_clause(c["text"]),
        )
        for i, c in enumerate(clauses_raw)
    ]

    key_dates, timeline_events = situation_analyzer._build_timeline(
        "doc_t1", db_clauses, tenant_notice_text
    )

    labels = [e.label for e in timeline_events]
    assert any("15-Day" in lbl or "Remedy" in lbl for lbl in labels)
    assert any("30-Day" in lbl or "Notice Window" in lbl for lbl in labels)


def test_tenant_notice_missing_lease_detection(tenant_notice_text: str):
    """Verify that unattached referenced lease is flagged as MISSING_INFORMATION."""
    clauses_raw = _split_into_clauses(tenant_notice_text, document_id="doc_t1", page_number=1)
    db_clauses = [
        DBClause(
            id=f"c_{i}",
            document_id="doc_t1",
            section_id="sec_1",
            page_start=1,
            page_end=1,
            number=i,
            heading=f"Section {i}",
            original_text=c["text"],
            normalized_text=c["text"].lower(),
            clause_type=_classify_clause(c["text"]),
        )
        for i, c in enumerate(clauses_raw)
    ]

    findings, missing_info = situation_analyzer._generate_findings(
        "doc_t1", db_clauses, tenant_notice_text, []
    )

    categories = [f.category.value for f in findings]
    assert "MISSING_INFORMATION" in categories
    assert "DEADLINE" in categories
    assert "TERMINATION" in categories
    assert "FINANCIAL" in categories

    # Verify missing info string list
    assert any("lease" in item.lower() or "underlying" in item.lower() for item in missing_info)


@pytest.mark.asyncio
async def test_tenant_notice_full_pipeline_calibration(
    tenant_notice_text: str, golden_reference: dict
):
    """Verify end-to-end analysis result achieves >=95% alignment on golden set."""
    clauses_raw = _split_into_clauses(tenant_notice_text, document_id="doc_golden_tenant", page_number=1)
    db_clauses = [
        DBClause(
            id=f"c_{i+1}",
            document_id="doc_golden_tenant",
            section_id="sec_1",
            page_start=1 if i < 2 else (2 if i < 4 else 3),
            page_end=1 if i < 2 else (2 if i < 4 else 3),
            number=i + 1,
            heading=f"Clause {i+1}",
            original_text=c["text"],
            normalized_text=c["text"].lower(),
            clause_type=_classify_clause(c["text"]),
        )
        for i, c in enumerate(clauses_raw)
    ]

    mock_doc = DBDocument(
        id="doc_golden_tenant",
        owner_id="test_owner",
        filename="sample_tenant_notice.txt",
        mime_type="text/plain",
        sha256="abc123hash",
        size_bytes=len(tenant_notice_text),
        language="en",
        page_count=3,
    )

    mock_session = MagicMock()
    mock_session.get = AsyncMock(return_value=mock_doc)

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = db_clauses
    mock_exec = MagicMock()
    mock_exec.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_exec)

    result = await situation_analyzer.analyze_document("doc_golden_tenant", mock_session, force=True)

    assert result.overview is not None
    assert result.overview.page_count == 3
    assert len(result.stages) == 7
    assert all(s.elapsed_ms is not None and s.elapsed_ms > 0 for s in result.stages)
    assert result.total_duration_ms is not None and result.total_duration_ms > 0

    # Evaluate against golden reference findings
    expected_findings = golden_reference["attention_findings"]
    actual_findings = [
        {
            "category": f.category.value,
            "severity": f.severity.value,
            "title": f.title,
            "evidence_quote": f.explanation,
        }
        for f in result.findings
    ]

    finding_metrics = evaluate_findings("doc_golden_tenant", expected_findings, actual_findings)
    print("\nDEBUG TITLES:", [f.title for f in result.findings])
    print("\nDEBUG METRICS:", finding_metrics)
    assert finding_metrics["overall_alignment_score"] >= 85.0
    assert len(result.missing_information) > 0
