"""
LegalLens API — Timeline Engine.

Aggregates DATE entities and builds chronologies of contractual events.
"""

from __future__ import annotations

from collections.abc import Sequence

import structlog

from app.models.analysis import Entity, TimelineEvent
from app.models.base import generate_prefixed_uuid

logger = structlog.get_logger()


class TimelineEngine:
    """Service to generate a chronological timeline of events."""

    def generate_timeline(
        self, document_id: str, analysis_id: str, entities: Sequence[Entity]
    ) -> list[TimelineEvent]:
        """
        Scan all DATE entities and generate TimelineEvent records.
        """
        events: list[TimelineEvent] = []

        # Filter for dates
        date_entities = [e for e in entities if e.entity_type == "DATE"]

        for entity in date_entities:
            # We use a very naive description generation for MVP
            # In a real system, the LLM would summarize the event based on the clause text

            event = TimelineEvent(
                id=generate_prefixed_uuid("tme"),
                analysis_id=analysis_id,
                document_id=document_id,
                date_value=entity.normalized_value,
                description=f"Event occurring on {entity.value}",
                event_type="UNSPECIFIED",
                related_entity_id=entity.id,
            )
            events.append(event)

        logger.info(
            "timeline_generation_complete",
            document_id=document_id,
            event_count=len(events),
        )
        return events
