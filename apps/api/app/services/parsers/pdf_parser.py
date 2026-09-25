"""
LegalLens API — PyMuPDF Parser.

Extracts text, layout blocks, and reading order from PDF files.
"""

from __future__ import annotations

import io
from typing import BinaryIO

import fitz  # PyMuPDF
import structlog

from packages.schemas.domain import CanonicalPage, TextBlock, TextSource

logger = structlog.get_logger()


def extract_pdf(
    file_bytes: bytes | BinaryIO,
    document_id: str,
) -> list[CanonicalPage]:
    """
    Parse a PDF file into canonical pages and text blocks.
    
    1. Loads the document via PyMuPDF.
    2. Iterates pages and extracts text dictionaries (blocks).
    3. Converts PyMuPDF blocks into CanonicalPage objects.
    """
    if isinstance(file_bytes, bytes):
        stream = io.BytesIO(file_bytes)
    else:
        stream = file_bytes
        stream.seek(0)

    try:
        doc = fitz.open(stream=stream, filetype="pdf")
    except Exception as e:
        logger.error("pdf_parsing_failed", document_id=document_id, error=str(e))
        raise ValueError(f"Failed to parse PDF: {e}") from e

    canonical_pages = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_num = page_index + 1
        
        # Get page dimensions
        rect = page.rect
        width, height = rect.width, rect.height

        # Extract text blocks
        # dict layout: { "blocks": [ { "type": 0, "bbox": [...], "lines": [...] }, ... ] }
        page_dict = page.get_text("dict")
        blocks_data = page_dict.get("blocks", [])

        canonical_blocks = []
        page_text_parts = []
        block_order = 0

        for block in blocks_data:
            # We only care about text blocks (type 0)
            if block.get("type") != 0:
                continue

            block_text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "") + " "
                block_text = block_text.rstrip() + "\n"
            
            block_text = block_text.strip()
            if not block_text:
                continue

            bbox = block.get("bbox", [0.0, 0.0, 0.0, 0.0])
            
            # Create canonical block
            canonical_block = TextBlock(
                block_id=f"{document_id}_p{page_num}_b{block_order}",
                text=block_text,
                bbox=bbox,
                order=block_order,
            )
            canonical_blocks.append(canonical_block)
            page_text_parts.append(block_text)
            block_order += 1

        # Combine block text into full page text
        full_page_text = "\n\n".join(page_text_parts)
        
        # In a real implementation, we would hash the page content
        import hashlib
        content_hash = hashlib.sha256(full_page_text.encode("utf-8")).hexdigest()

        # If native extraction yields too little text, mark for OCR
        # This is a simple heuristic
        text_source = TextSource.NATIVE_TEXT
        if len(full_page_text.strip()) < 50 and len(canonical_blocks) < 2:
            # Likely a scanned image
            # In a real pipeline, we'd trigger OCR here
            pass

        canonical_page = CanonicalPage(
            page_id=f"{document_id}_p{page_num}",
            page_number=page_num,
            text=full_page_text,
            text_source=text_source,
            width=width,
            height=height,
            blocks=canonical_blocks,
            content_hash=content_hash,
        )
        canonical_pages.append(canonical_page)

    doc.close()
    return canonical_pages
