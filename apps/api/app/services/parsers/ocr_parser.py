"""
LegalLens API — OCR Parser.

Uses Tesseract OCR to extract text from images or scanned PDFs.
"""

from __future__ import annotations

import io
from typing import BinaryIO

import structlog

from packages.schemas.domain import CanonicalPage

# We will need pytesseract and something to convert PDF to images (e.g. pdf2image)
# import pytesseract
# from pdf2image import convert_from_bytes

logger = structlog.get_logger()


def extract_ocr(
    file_bytes: bytes | BinaryIO,
    document_id: str,
) -> list[CanonicalPage]:
    """
    Perform OCR on a document to extract text.
    
    Currently a stub. In a full implementation, this would:
    1. Convert PDF pages to images.
    2. Run pytesseract on each image to extract text and bboxes.
    3. Construct CanonicalPage objects.
    """
    logger.warning("ocr_extraction_not_implemented", document_id=document_id)
    # Placeholder for actual OCR implementation
    return []
