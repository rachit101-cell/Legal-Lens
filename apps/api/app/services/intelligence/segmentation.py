"""
LegalLens API — Segmentation Service.

Heuristically segments document pages into logical Sections and Clauses.
In a full production environment, this could be augmented by NLP/AI models.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

import structlog

from app.models.analysis import Clause, Section
from app.models.base import generate_prefixed_uuid
from app.models.document import Page

logger = structlog.get_logger()

# Basic regex for catching section headers like "1. DEFINITIONS", "ARTICLE I", etc.
SECTION_PATTERN = re.compile(
    r"^(?:ARTICLE|SECTION)\s+[IVX\d]+[\.\-]?\s+(.*)$|^(\d+\.)\s+([A-Z\s]+)$",
    re.IGNORECASE,
)


class SegmentationService:
    """Service to segment pages into sections and clauses."""

    def segment_document(
        self, document_id: str, pages: Sequence[Page]
    ) -> tuple[list[Section], list[Clause]]:
        """
        Process pages to identify logical sections and clauses.
        Returns a tuple of (Sections, Clauses).
        """
        sections: list[Section] = []
        clauses: list[Clause] = []

        current_section = None
        clause_order = 0
        section_order = 0

        # Sort pages by page number
        sorted_pages = sorted(pages, key=lambda p: p.page_number)

        for page in sorted_pages:
            # We assume blocks are stored as JSON list in page.blocks
            blocks = sorted(page.blocks, key=lambda b: b.get("order", 0))

            for block in blocks:
                text = block.get("text", "").strip()
                if not text:
                    continue

                # Check if it's a section header
                # We use a simple heuristic: short text, matches pattern or is all caps
                is_header = False
                title = text

                if len(text) < 150:
                    match = SECTION_PATTERN.match(text)
                    if match or (text.isupper() and len(text.split()) < 10):
                        is_header = True

                if is_header:
                    # Create new section
                    current_section = Section(
                        id=generate_prefixed_uuid("sec"),
                        document_id=document_id,
                        title=title[:255],
                        sequence_order=section_order,
                        level=1,
                        source_page_ids=[page.id],
                    )
                    sections.append(current_section)
                    section_order += 1
                else:
                    # Treat as a clause in the current section
                    clause = Clause(
                        id=generate_prefixed_uuid("cls"),
                        document_id=document_id,
                        section_id=current_section.id if current_section else None,
                        text=text,
                        sequence_order=clause_order,
                        source_page_id=page.id,
                        source_block_id=block.get("block_id"),
                        taxonomy_class=None,  # Filled later by Taxonomy service
                    )
                    clauses.append(clause)

                    if current_section and page.id not in current_section.source_page_ids:
                        current_section.source_page_ids.append(page.id)

                    clause_order += 1

        logger.info(
            "segmentation_complete",
            document_id=document_id,
            section_count=len(sections),
            clause_count=len(clauses),
        )
        return sections, clauses
