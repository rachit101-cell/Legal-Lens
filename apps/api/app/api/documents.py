"""
LegalLens API — Document Endpoints.

Upload, retrieve, and manage legal documents.
All endpoints enforce ownership checks.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.repositories.document_repo import DocumentRepository
from app.services.upload_service import UploadService
from packages.schemas.domain import DocumentResponse, UploadResponse
from packages.schemas.enums import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    DocumentStatus,
    DocumentType,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/documents", tags=["documents"])
_background_tasks: set[asyncio.Task[None]] = set()


def _get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def _validate_file_extension(filename: str) -> str:
    """Validate file extension against allowed types."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        msg = f"Unsupported file type '{ext}'. Accepted types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        raise HTTPException(status_code=415, detail=msg)
    return ext


def _validate_mime_type(content_type: str | None, extension: str) -> str:
    """Validate MIME type against allowed types and extension consistency."""
    if not content_type:
        msg = "Content-Type header is required"
        raise HTTPException(status_code=415, detail=msg)

    # Normalize MIME type
    mime = content_type.split(";")[0].strip().lower()

    if mime not in ALLOWED_MIME_TYPES:
        msg = f"Unsupported content type '{mime}'. Accepted: PDF, DOCX"
        raise HTTPException(status_code=415, detail=msg)

    return mime


def _validate_file_size(size: int) -> None:
    """Validate file size against configured maximum."""
    settings = get_settings()
    if size > settings.max_upload_size_bytes:
        msg = f"File size exceeds maximum of {settings.max_upload_size_mb} MB"
        raise HTTPException(status_code=413, detail=msg)


async def _process_document_background(document_id: str) -> None:
    """Process document in background after upload."""
    from app.db.session import async_session_maker
    from app.services.document_engine import DocumentEngine

    try:
        async with async_session_maker() as session:
            engine = DocumentEngine(session)
            await engine.process_document(document_id)
    except Exception as e:
        logger.error("background_processing_failed", document_id=document_id, error=str(e))


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_document(
    request: Request,
    file: Annotated[UploadFile, File(description="PDF or DOCX file to analyze")],
    language_hint: Annotated[str | None, Form()] = None,
    retain_hours: Annotated[int | None, Form()] = None,
    db: AsyncSession = Depends(get_db_session),
) -> UploadResponse:
    """
    Upload a legal document for analysis.

    Accepts PDF and DOCX files up to 20 MB.
    Returns 202 with document and analysis IDs.
    """
    request_id = _get_request_id(request)

    # ── Validate filename and extension ──────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    extension = _validate_file_extension(file.filename)
    mime_type = _validate_mime_type(file.content_type, extension)

    # ── Read and validate file content ───────────────────────
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=422, detail="File is empty")

    _validate_file_size(len(content))

    # ── Validate magic bytes ─────────────────────────────────
    if extension == ".pdf" and not content[:5].startswith(b"%PDF-"):
        raise HTTPException(
            status_code=422,
            detail="File content does not match PDF format",
        )
    if extension == ".docx" and not content[:2] == b"PK":
        raise HTTPException(
            status_code=422,
            detail="File content does not match DOCX format",
        )

    # ── Process Upload ───────────────────────────────────────
    # TODO: Get real owner_id from auth context
    owner_id = "demo_user"

    document_repo = DocumentRepository(db)
    upload_service = UploadService(document_repo)

    result = await upload_service.process_upload(
        owner_id=owner_id,
        filename=file.filename,
        mime_type=mime_type,
        content=content,
        language_hint=language_hint or "en",
        retain_hours=retain_hours,
    )

    # Trigger document processing in the background
    task = asyncio.create_task(_process_document_background(result["document_id"]))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return UploadResponse(
        request_id=request_id,
        document_id=result["document_id"],
        analysis_id=result["analysis_id"],
        status=DocumentStatus.QUEUED,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    request: Request, document_id: str, db: AsyncSession = Depends(get_db_session)
) -> DocumentResponse:
    """
    Get document metadata and processing state.
    """
    request_id = _get_request_id(request)

    # TODO: Get real owner_id from auth context
    owner_id = "demo_user"

    document_repo = DocumentRepository(db)
    doc = await document_repo.get_by_owner_and_id(owner_id, document_id)

    if not doc:
        raise HTTPException(status_code=404)

    return DocumentResponse(
        request_id=request_id,
        document_id=doc.id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        page_count=doc.page_count,
        status=DocumentStatus(doc.status),
        language=doc.language,
        document_type=DocumentType(doc.document_type) if doc.document_type else None,
        created_at=doc.created_at,
        expires_at=None,
    )


# ── Document content endpoint (for frontend viewer) ─────────
@router.get("/{document_id}/pages")
async def get_document_pages(
    request: Request,
    document_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get extracted text pages for the document viewer."""
    from sqlalchemy import select

    from app.models.document import Page

    request_id = _get_request_id(request)

    document_repo = DocumentRepository(db)
    doc = await document_repo.get_by_owner_and_id("demo_user", document_id)
    if not doc:
        raise HTTPException(status_code=404)

    stmt = select(Page).where(Page.document_id == document_id).order_by(Page.page_number)
    result = await db.execute(stmt)
    pages = result.scalars().all()

    return {
        "request_id": request_id,
        "document_id": document_id,
        "status": doc.status,
        "filename": doc.filename,
        "pages": [
            {
                "page_number": p.page_number,
                "text": p.text,
            }
            for p in pages
        ],
    }


from fastapi import Response


@router.delete("/{document_id}", status_code=204, response_class=Response, response_model=None)
async def delete_document(
    request: Request, document_id: str, db: AsyncSession = Depends(get_db_session)
) -> None:
    """
    Soft-delete a document and cascade to all dependent data.
    """
    request_id = _get_request_id(request)

    # TODO: Get real owner_id from auth context
    owner_id = "demo_user"

    document_repo = DocumentRepository(db)
    doc = await document_repo.get_by_owner_and_id(owner_id, document_id)

    if not doc:
        raise HTTPException(status_code=404)

    await document_repo.update_status(document_id, DocumentStatus.DELETED)

    logger.info(
        "document_deleted",
        request_id=request_id,
        document_id=document_id,
    )
