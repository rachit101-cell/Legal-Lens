"""
LegalLens API — Upload Service.

Handles business logic for secure file uploading, storage, and database recording.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import BinaryIO

import structlog

from app.core.config import get_settings
from app.models.base import generate_prefixed_uuid
from app.models.document import Document
from app.repositories.document_repo import DocumentRepository
from app.services.storage import storage_service
from packages.schemas.enums import DocumentStatus

logger = structlog.get_logger()


class UploadService:
    """Service for handling document uploads."""

    def __init__(self, document_repo: DocumentRepository) -> None:
        """Initialize with required repositories."""
        self.document_repo = document_repo
        self.settings = get_settings()

    async def process_upload(
        self,
        owner_id: str,
        filename: str,
        mime_type: str,
        content: bytes | BinaryIO,
        language_hint: str = "en",
        retain_hours: int | None = None,
    ) -> dict[str, str]:
        """
        Process an uploaded document.

        1. Calculates SHA-256
        2. Uploads to secure private storage
        3. Creates the Document record in the database

        Returns a dict with document_id and analysis_id.
        """
        # Read content if it's a file-like object and calculate hash
        if not isinstance(content, bytes):
            content = content.read()

        sha256 = hashlib.sha256(content).hexdigest()
        size_bytes = len(content)

        # Generate IDs
        doc_id = generate_prefixed_uuid("doc")
        analysis_id = generate_prefixed_uuid("run")

        # Determine storage key
        # Format: documents/{owner_id}/{doc_id}.pdf
        storage_key = f"documents/{owner_id}/{doc_id}"

        # 1. Upload to storage
        logger.info("uploading_to_storage", document_id=doc_id, size=size_bytes)
        storage_service.put_private(
            object_name=storage_key,
            data=content,
            content_type=mime_type,
        )

        # 2. Create DB Record
        ttl = retain_hours or self.settings.document_ttl_hours
        expires_at = datetime.utcnow() + timedelta(hours=ttl)
        logger.info("document_retention_ttl_set", ttl_hours=ttl, expires_at=expires_at.isoformat())

        document = Document(
            id=doc_id,
            owner_id=owner_id,
            filename=filename,
            mime_type=mime_type,
            sha256=sha256,
            size_bytes=size_bytes,
            status=DocumentStatus.QUEUED,
            language=language_hint,
            storage_path=storage_key,
            analysis_id=analysis_id,
        )

        # We don't have expire_at on Document model right now, it's just soft delete.
        # So we skip assigning expires_at to the model for now (it will be handled by TTL job based on created_at or we add it later)

        await self.document_repo.create(document)

        logger.info(
            "document_created",
            document_id=doc_id,
            analysis_id=analysis_id,
            owner_id=owner_id,
        )

        return {
            "document_id": doc_id,
            "analysis_id": analysis_id,
        }
