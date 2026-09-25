"""
LegalLens API — Entity Extraction Service.

Extracts named entities (Parties, Dates, Amounts) from clauses.
"""

from __future__ import annotations

import re
from typing import Sequence

import structlog

from app.models.analysis import Clause, Entity
from app.models.base import generate_prefixed_uuid

logger = structlog.get_logger()

# Basic regex heuristics for MVP. 
# In production, this would be backed by an LLM (e.g. OpenAI/Anthropic) or a specialized NLP model (spaCy).
DATE_PATTERN = re.compile(r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", re.IGNORECASE)
AMOUNT_PATTERN = re.compile(r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:Dollars|USD)\b", re.IGNORECASE)


class EntityExtractionService:
    """Service to extract legal entities from text."""

    def extract_entities(self, document_id: str, clauses: Sequence[Clause]) -> list[Entity]:
        """
        Scan clauses and extract entities.
        Returns a list of Entity objects.
        """
        entities: list[Entity] = []

        for clause in clauses:
            text = clause.text
            
            # Extract Dates
            for match in DATE_PATTERN.finditer(text):
                value = match.group(0)
                entities.append(
                    Entity(
                        id=generate_prefixed_uuid("ent"),
                        document_id=document_id,
                        clause_id=clause.id,
                        entity_type="DATE",
                        value=value,
                        normalized_value=value, # In real system, normalize to ISO8601
                        source_text=value,
                        confidence=0.8,
                    )
                )
                
            # Extract Amounts
            for match in AMOUNT_PATTERN.finditer(text):
                value = match.group(0)
                entities.append(
                    Entity(
                        id=generate_prefixed_uuid("ent"),
                        document_id=document_id,
                        clause_id=clause.id,
                        entity_type="MONEY",
                        value=value,
                        normalized_value=value, # Strip commas/symbols
                        source_text=value,
                        confidence=0.8,
                    )
                )
                
            # Naive Party Extraction (Looking for "Company, Inc.", "LLC")
            party_pattern = re.compile(r"\b([A-Z][a-zA-Z0-9\s]+(?:Inc\.|LLC|Ltd\.|Corporation|Company))\b")
            for match in party_pattern.finditer(text):
                value = match.group(0)
                entities.append(
                    Entity(
                        id=generate_prefixed_uuid("ent"),
                        document_id=document_id,
                        clause_id=clause.id,
                        entity_type="PARTY",
                        value=value,
                        normalized_value=value,
                        source_text=value,
                        confidence=0.7,
                    )
                )

        logger.info(
            "entity_extraction_complete",
            document_id=document_id,
            entity_count=len(entities),
        )
        return entities
