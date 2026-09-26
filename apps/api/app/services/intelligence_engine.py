"""
LegalLens API — Intelligence Engine.

Orchestrates the Legal Intelligence pipeline:
1. Segmentation (Sections & Clauses)
2. Taxonomy Classification
3. Entity Extraction
"""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Page
from app.repositories.analysis_repo import AnalysisRepository
from app.services.analysis.finding_engine import FindingEngine
from app.services.analysis.timeline_engine import TimelineEngine
from app.services.intelligence.entity_extraction import EntityExtractionService
from app.services.intelligence.segmentation import SegmentationService
from app.services.intelligence.taxonomy import TaxonomyService
from packages.schemas.enums import AnalysisStatus

logger = structlog.get_logger()


class IntelligenceEngine:
    """Orchestrates legal intelligence extraction."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.session = db_session
        self.analysis_repo = AnalysisRepository(db_session)
        self.segmentation_service = SegmentationService()
        self.taxonomy_service = TaxonomyService()
        self.entity_service = EntityExtractionService()
        self.finding_engine = FindingEngine()
        self.timeline_engine = TimelineEngine()

    async def run_analysis(self, analysis_id: str, document_id: str) -> None:
        """
        Run the complete legal intelligence pipeline.
        """
        logger.info(
            "intelligence_analysis_started", analysis_id=analysis_id, document_id=document_id
        )

        try:
            # Mark as running
            await self.analysis_repo.update_run_status(analysis_id, AnalysisStatus.RUNNING)

            # Fetch all pages for the document
            result = await self.session.execute(select(Page).where(Page.document_id == document_id))
            pages = result.scalars().all()

            if not pages:
                logger.warning("no_pages_found_for_analysis", document_id=document_id)
                await self.analysis_repo.update_run_status(analysis_id, AnalysisStatus.COMPLETED)
                return

            # 1. Segmentation
            sections, clauses = self.segmentation_service.segment_document(document_id, pages)

            # 2. Taxonomy Classification
            self.taxonomy_service.classify_clauses(clauses)

            # 3. Entity Extraction
            entities = self.entity_service.extract_entities(document_id, clauses)

            # 3.5 Generate Embeddings
            # In a real app we'd do this in batch
            from app.services.retrieval.embedding_service import embedding_service

            for clause in clauses:
                clause.embedding = embedding_service.embed_text(clause.text)

            # 4. Findings Generation
            findings = self.finding_engine.generate_findings(
                document_id, analysis_id, clauses, entities
            )

            # 5. Timeline Generation
            timeline_events = self.timeline_engine.generate_timeline(
                document_id, analysis_id, entities
            )

            # 6. Save to Database
            # Assign analysis_id to all generated entities
            for s in sections:
                s.analysis_id = analysis_id
            for c in clauses:
                c.analysis_id = analysis_id
            for e in entities:
                e.analysis_id = analysis_id

            await self.analysis_repo.save_sections(sections)
            await self.analysis_repo.save_clauses(clauses)
            await self.analysis_repo.save_entities(entities)
            await self.analysis_repo.save_findings(findings)
            await self.analysis_repo.save_timeline_events(timeline_events)

            # Mark as completed
            await self.analysis_repo.update_run_status(analysis_id, AnalysisStatus.COMPLETED)

            logger.info(
                "intelligence_analysis_completed", analysis_id=analysis_id, document_id=document_id
            )

        except Exception as e:
            logger.error("intelligence_analysis_failed", analysis_id=analysis_id, error=str(e))
            await self.session.rollback()
            await self.analysis_repo.update_run_status(analysis_id, AnalysisStatus.FAILED)
            raise
