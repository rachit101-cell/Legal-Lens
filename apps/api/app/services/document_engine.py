"""
LegalLens API — Document Engine.

Orchestrates the extraction of text from raw documents (PDF/DOCX)
and populates the Canonical Document Model in the database,
including auto-creating clauses from extracted text blocks.
"""

from __future__ import annotations

import hashlib
import re

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Clause
from app.models.base import generate_prefixed_uuid
from app.models.document import Document, Page
from app.repositories.document_repo import DocumentRepository
from app.services.parsers.docx_parser import extract_docx
from app.services.parsers.pdf_parser import extract_pdf
from app.services.storage import storage_service
from packages.schemas.enums import ClauseType, DocumentStatus

logger = structlog.get_logger()


def _classify_clause(text: str) -> ClauseType:
    """Deterministic legal clause taxonomy classification with heading and context awareness."""
    lower = text.lower().strip()
    first_line = lower.split("\n")[0] if "\n" in lower else lower

    # Check headings or titles first
    if any(w in first_line for w in ["terminate", "termination", "cancellation"]):
        return ClauseType.TERMINATION_NOTICE
    if any(re.search(rf"\b{re.escape(w)}\b", first_line) for w in ["term", "terms", "renewal", "expiration", "duration"]):
        return ClauseType.TERM_RENEWAL
    if any(w in first_line for w in ["governing law", "jurisdiction", "governed by", "dispute"]):
        return ClauseType.DISPUTE_GOVERNING_LAW
    if any(w in first_line for w in ["confidential", "non-disclosure", "nda", "proprietary"]):
        return ClauseType.CONFIDENTIALITY_IP
    if any(w in first_line for w in ["liability", "indemnif", "hold harmless"]):
        return ClauseType.LIABILITY_INDEMNITY
    if any(w in first_line for w in ["payment", "fees", "rent", "compensation"]):
        return ClauseType.PAYMENT_FEES

    # Body text matching
    if any(w in lower for w in ["governing law", "jurisdiction", "governed by", "construed in accordance"]):
        return ClauseType.DISPUTE_GOVERNING_LAW
    if any(w in lower for w in ["maximum liability", "limitation of liability", "indemnif", "hold harmless"]):
        return ClauseType.LIABILITY_INDEMNITY
    if any(w in lower for w in ["terminate", "termination", "cancel"]):
        return ClauseType.TERMINATION_NOTICE
    if any(re.search(rf"\b{re.escape(w)}\b", lower) for w in ["expire three", "expire", "renewal", "initial term", "extended term"]):
        return ClauseType.TERM_RENEWAL
    if any(w in lower for w in ["confidential information", "non-disclosure", "nda", "proprietary"]):
        return ClauseType.CONFIDENTIALITY_IP
    if any(w in lower for w in ["payment", "fee", "compensation", "amount", "pay"]):
        return ClauseType.PAYMENT_FEES
    if any(w in lower for w in ["warrant", "representation", "guarantee"]):
        return ClauseType.BOILERPLATE
    if any(w in lower for w in ["obligation", "shall", "must", "required to"]):
        return ClauseType.MISCELLANEOUS
    if any(w in lower for w in ["definition", "means", "defined as", "herein"]):
        return ClauseType.MISCELLANEOUS
    return ClauseType.OTHER


def _split_into_clauses(full_text: str, document_id: str, page_number: int) -> list[dict]:
    """Split page text into clause-like segments."""
    # Try to split by numbered sections (1., 2., etc.) or paragraph breaks
    # First try numbered pattern
    parts = re.split(r'\n(?=\d+[\.\)]\s)', full_text)
    
    if len(parts) <= 1:
        # Try splitting by double newlines (paragraphs)
        parts = [p.strip() for p in full_text.split('\n\n') if p.strip()]
    
    if not parts:
        parts = [full_text.strip()] if full_text.strip() else []
    
    clauses = []
    for i, part in enumerate(parts):
        part = part.strip()
        if len(part) < 10:  # Skip very short fragments
            continue
            
        # Try to extract heading
        lines = part.split('\n', 1)
        heading = None
        if len(lines) > 1 and len(lines[0]) < 100:
            heading = lines[0].strip()
            
        clauses.append({
            "text": part,
            "heading": heading,
            "number": str(i + 1),
            "page": page_number,
        })
    
    return clauses


class DocumentEngine:
    """Orchestrates document parsing and DB insertion."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize with an async database session."""
        self.session = db_session
        self.document_repo = DocumentRepository(db_session)

    async def process_document(self, document_id: str) -> None:
        """
        Main pipeline for processing a queued document.
        
        1. Fetch document metadata.
        2. Download raw file from MinIO.
        3. Parse into canonical structure (Pages -> Blocks).
        4. Create clauses from extracted text.
        5. Save to PostgreSQL.
        6. Update status to READY.
        """
        logger.info("document_processing_started", document_id=document_id)
        
        # 1. Fetch document
        doc = await self.document_repo.get(document_id)
        if not doc:
            logger.error("document_not_found", document_id=document_id)
            return
            
        if doc.status != DocumentStatus.QUEUED:
            logger.warning("document_not_queued", document_id=document_id, status=doc.status)
            return
            
        try:
            # Update status to processing
            await self.document_repo.update_status(document_id, DocumentStatus.EXTRACTING)
            
            # 2. Download from storage
            raw_bytes = storage_service.get_private(doc.storage_path)
            
            # 3. Parse Document
            canonical_pages = []
            if doc.mime_type == "application/pdf":
                canonical_pages = extract_pdf(raw_bytes, document_id)
            elif doc.mime_type in (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"
            ):
                canonical_pages = extract_docx(raw_bytes, document_id)
            else:
                raise ValueError(f"Unsupported MIME type for extraction: {doc.mime_type}")
                
            # 4. Save Pages and create Clauses
            all_clauses = []
            
            for p in canonical_pages:
                page_record = Page(
                    id=p.page_id,
                    document_id=document_id,
                    page_number=p.page_number,
                    text=p.text,
                    text_source=p.text_source,
                    width=p.width,
                    height=p.height,
                    blocks=[b.model_dump(mode="json") for b in p.blocks],
                    content_hash=p.content_hash,
                )
                self.session.add(page_record)
                
                # Create clauses from this page's text
                clause_dicts = _split_into_clauses(p.text, document_id, p.page_number)
                for cd in clause_dicts:
                    clause = Clause(
                        id=generate_prefixed_uuid("cl"),
                        document_id=document_id,
                        number=cd["number"],
                        heading=cd["heading"],
                        original_text=cd["text"],
                        normalized_text=cd["text"].lower().strip(),
                        page_start=cd["page"],
                        page_end=cd["page"],
                        clause_type=_classify_clause(cd["text"]),
                        classification_confidence=0.8,
                    )
                    self.session.add(clause)
                    all_clauses.append(clause)
            
            # Update document stats
            doc.page_count = len(canonical_pages)
            
            # 5. Commit all changes and mark as COMPLETED
            await self.session.commit()
            await self.document_repo.update_status(document_id, DocumentStatus.COMPLETED)
            
            logger.info(
                "document_processing_complete",
                document_id=document_id,
                page_count=doc.page_count,
                clause_count=len(all_clauses),
            )

        except Exception as e:
            logger.error("document_processing_failed", document_id=document_id, error=str(e))
            await self.session.rollback()
            await self.document_repo.update_status(document_id, DocumentStatus.FAILED)
