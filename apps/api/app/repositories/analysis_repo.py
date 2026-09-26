"""
LegalLens API — Analysis Repository.

Data access layer for AnalysisRuns, Sections, Clauses, and Entities.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisRun, Clause, Entity, Finding, Section, TimelineEvent
from packages.schemas.enums import AnalysisStatus


class AnalysisRepository:
    """Repository for Analysis and Legal Intelligence entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, analysis_id: str) -> AnalysisRun | None:
        """Get an analysis run by ID."""
        result = await self.session.execute(
            select(AnalysisRun).where(AnalysisRun.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def create_run(self, run: AnalysisRun) -> AnalysisRun:
        """Create a new analysis run."""
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def update_run_status(self, analysis_id: str, status: AnalysisStatus) -> None:
        """Update the status of an analysis run."""
        run = await self.get_run(analysis_id)
        if run:
            run.status = status  # type: ignore[assignment]
            await self.session.commit()

    async def save_sections(self, sections: list[Section]) -> None:
        """Bulk save sections."""
        self.session.add_all(sections)
        await self.session.commit()

    async def save_clauses(self, clauses: list[Clause]) -> None:
        """Bulk save clauses."""
        self.session.add_all(clauses)
        await self.session.commit()

    async def save_entities(self, entities: list[Entity]) -> None:
        """Bulk save entities."""
        self.session.add_all(entities)
        await self.session.commit()

    async def save_findings(self, findings: list[Finding]) -> None:
        """Bulk save findings."""
        self.session.add_all(findings)
        await self.session.commit()

    async def save_timeline_events(self, events: list[TimelineEvent]) -> None:
        """Bulk save timeline events."""
        self.session.add_all(events)
        await self.session.commit()

    async def get_sections_by_document(self, document_id: str) -> Sequence[Section]:
        """Get all sections for a document, ordered by sequence."""
        result = await self.session.execute(
            select(Section)
            .where(Section.document_id == document_id)
            .order_by(Section.sequence_order)
        )
        return result.scalars().all()

    async def get_clauses_by_document(self, document_id: str) -> Sequence[Clause]:
        """Get all clauses for a document."""
        result = await self.session.execute(
            select(Clause).where(Clause.document_id == document_id).order_by(Clause.sequence_order)
        )
        return result.scalars().all()

    async def get_entities_by_document(self, document_id: str) -> Sequence[Entity]:
        """Get all entities for a document."""
        result = await self.session.execute(select(Entity).where(Entity.document_id == document_id))
        return result.scalars().all()

    async def get_findings_by_analysis(self, analysis_id: str) -> Sequence[Finding]:
        """Get all findings for an analysis run."""
        result = await self.session.execute(
            select(Finding).where(Finding.analysis_id == analysis_id)
        )
        return result.scalars().all()

    async def get_timeline_by_analysis(self, analysis_id: str) -> Sequence[TimelineEvent]:
        """Get timeline events for an analysis run, ordered by date."""
        # For now we order by raw date_value string; in a real system this would be a proper date field
        result = await self.session.execute(
            select(TimelineEvent)
            .where(TimelineEvent.analysis_id == analysis_id)
            .order_by(TimelineEvent.date_value)
        )
        return result.scalars().all()
