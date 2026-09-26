"""
LegalLens API — Retention Policy Enforcer.

Implements the zero-retention policy by scrubbing documents and analysis
data after the 24-hour TTL expires.
"""

from __future__ import annotations

import datetime

import structlog
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document

logger = structlog.get_logger()


class RetentionService:
    """Service to scrub expired data."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.session = db_session

    async def scrub_expired_documents(self) -> int:
        """
        Delete all documents (and cascaded data) older than 24 hours.
        Returns the number of documents deleted.
        """
        threshold = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=24)

        # In SQLAlchemy, if cascade="all, delete-orphan" is set on relationships,
        # deleting the parent Document will cascade to AnalysisRuns, Pages, Clauses, etc.
        stmt = delete(Document).where(Document.created_at < threshold)

        result = await self.session.execute(stmt)
        await self.session.commit()

        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info("retention_scrub_completed", deleted_documents=deleted_count)

        return deleted_count
