"""
LegalLens API — Document Repository.

Data access layer for documents.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from packages.schemas.enums import DocumentStatus


class DocumentRepository:
    """Repository for Document entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async database session."""
        self.session = session

    async def get(self, document_id: str) -> Document | None:
        """Get a document by ID."""
        result = await self.session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def get_by_owner_and_id(self, owner_id: str, document_id: str) -> Document | None:
        """Get a document by ID and owner."""
        result = await self.session.execute(
            select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def create(self, document: Document) -> Document:
        """Create a new document record."""
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def update_status(self, document_id: str, status: DocumentStatus) -> None:
        """Update the status of a document."""
        document = await self.get(document_id)
        if document:
            document.status = status  # type: ignore[assignment]
            await self.session.commit()

    async def get_by_owner(
        self, owner_id: str, limit: int = 50, offset: int = 0
    ) -> Sequence[Document]:
        """List documents for an owner."""
        result = await self.session.execute(
            select(Document)
            .where(
                Document.owner_id == owner_id,
                Document.status != DocumentStatus.DELETED,
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
