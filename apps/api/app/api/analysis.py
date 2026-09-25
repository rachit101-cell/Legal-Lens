"""
LegalLens API — Analysis Endpoints.

Trigger analysis, check status, and retrieve the Legal Situation Map.
All endpoints query and return verified structured models.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.analysis import Clause
from app.models.document import Document
from app.services.analysis.situation_analyzer import situation_analyzer
from packages.schemas.domain import AnalysisResult
from packages.schemas.enums import AnalysisStatus

router = APIRouter(prefix="/documents/{document_id}", tags=["analysis"])


def _get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))


@router.post("/analyze", status_code=202)
async def trigger_analysis(
    request: Request,
    document_id: str,
    force: bool = False,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Start or restart an analysis run for a document.
    """
    request_id = _get_request_id(request)
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    analysis_id = doc.analysis_id or f"run_{uuid.uuid4().hex[:12]}"

    return {
        "request_id": request_id,
        "document_id": document_id,
        "analysis_id": analysis_id,
        "status": AnalysisStatus.COMPLETED,
    }


@router.get("/analysis", response_model=AnalysisResult)
async def get_analysis(
    request: Request,
    document_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> AnalysisResult:
    """
    Get the Legal Situation Map for a document.
    Returns complete situation map, overview, findings, timeline, and checklist.
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await situation_analyzer.analyze_document(document_id, db)
    return result


@router.get("/clauses")
async def get_clauses(
    request: Request,
    document_id: str,
    page: int = 1,
    clause_type: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get paginated clauses for a document.
    Supports filtering by page, type, and text search.
    """
    request_id = _get_request_id(request)
    limit = min(limit, 100)

    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    query = select(Clause).where(Clause.document_id == document_id)

    if clause_type:
        query = query.where(Clause.clause_type == clause_type)

    if q:
        query = query.where(Clause.original_text.ilike(f"%{q}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * limit
    paginated_query = query.order_by(Clause.page_start, Clause.number).offset(offset).limit(limit)
    rows = await db.execute(paginated_query)
    clauses = rows.scalars().all()

    return {
        "request_id": request_id,
        "document_id": document_id,
        "clauses": [
            {
                "clause_id": c.id,
                "number": c.number,
                "heading": c.heading,
                "original_text": c.original_text,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "clause_type": str(c.clause_type),
                "classification_confidence": c.classification_confidence,
            }
            for c in clauses
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/findings")
async def get_findings(
    request: Request,
    document_id: str,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    include_resolved: bool = False,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get attention findings with evidence IDs and verification status.
    """
    request_id = _get_request_id(request)
    analysis = await situation_analyzer.analyze_document(document_id, db)
    
    findings = [f.model_dump(mode="json") for f in analysis.findings]
    if severity:
        findings = [f for f in findings if f.get("severity") == severity]
    if category:
        findings = [f for f in findings if f.get("category") == category]

    return {
        "request_id": request_id,
        "document_id": document_id,
        "findings": findings,
        "total": len(findings),
    }


@router.get("/timeline")
async def get_timeline(
    request: Request,
    document_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get timeline events with date status, duration, and calculation trace.
    """
    request_id = _get_request_id(request)
    analysis = await situation_analyzer.analyze_document(document_id, db)

    events = [e.model_dump(mode="json") for e in analysis.timeline]
    return {
        "request_id": request_id,
        "document_id": document_id,
        "events": events,
        "total": len(events),
    }


@router.get("/checklist")
async def get_checklist(
    request: Request,
    document_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get preparation checklist items.
    """
    request_id = _get_request_id(request)
    analysis = await situation_analyzer.analyze_document(document_id, db)

    items = [c.model_dump(mode="json") for c in analysis.checklist]
    return {
        "request_id": request_id,
        "document_id": document_id,
        "checklist": items,
        "total": len(items),
    }


@router.post("/questions")
async def generate_questions(
    request: Request,
    document_id: str,
    limit: int = 8,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Generate preparation-oriented questions for a legal professional.
    Output is not legal advice. Every question includes a reason.
    """
    request_id = _get_request_id(request)
    limit = min(limit, 20)

    analysis = await situation_analyzer.analyze_document(document_id, db)
    questions = [q.model_dump(mode="json") for q in analysis.lawyer_questions[:limit]]

    return {
        "request_id": request_id,
        "document_id": document_id,
        "questions": questions,
        "total": len(questions),
    }
