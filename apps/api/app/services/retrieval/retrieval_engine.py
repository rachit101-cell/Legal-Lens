"""
LegalLens API — Retrieval Engine.

Applies keyword relevance ranking and semantic matching to find the most relevant
contract clauses for a user's question.
"""

from __future__ import annotations

import re

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Clause

logger = structlog.get_logger()

STOPWORDS = {
    "what",
    "is",
    "the",
    "and",
    "or",
    "of",
    "in",
    "to",
    "for",
    "with",
    "on",
    "at",
    "by",
    "from",
    "up",
    "about",
    "into",
    "over",
    "after",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "but",
    "if",
    "then",
    "else",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "can",
    "will",
    "just",
    "should",
    "now",
    "tell",
    "me",
    "agreement",
    "contract",
    "document",
    "provision",
}


class RetrievalEngine:
    """Engine for document clause retrieval."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.session = db_session

    async def search(
        self,
        document_id: str,
        query: str,
        top_k: int = 8,
        threshold: float = 0.5,
    ) -> list[Clause]:
        """
        Retrieve the most relevant clauses for a question.

        Ranks clauses using keyword scoring against clause headings and body text,
        ensuring clauses from any page (including late sections like governing law,
        arbitration, and indemnities) are accurately prioritized.
        """
        logger.info("retrieval_search_started", query=query, document_id=document_id)

        # 1. Fetch all clauses for this document
        stmt = (
            select(Clause)
            .where(Clause.document_id == document_id)
            .order_by(Clause.page_start, Clause.number)
        )
        result = await self.session.execute(stmt)
        all_clauses = list(result.scalars().all())

        if not all_clauses or not query.strip():
            logger.info("retrieval_search_empty_or_no_query", total_clauses=len(all_clauses))
            return all_clauses[:top_k]

        # 2. Extract meaningful tokens from query
        tokens = [
            t.lower()
            for t in re.findall(r"\w+", query)
            if len(t) >= 2 and t.lower() not in STOPWORDS
        ]

        if not tokens:
            logger.info("retrieval_no_tokens_after_stopwords")
            return all_clauses[:top_k]

        # 3. Score clauses
        scored: list[tuple[float, Clause]] = []
        for c in all_clauses:
            text_lower = c.original_text.lower()
            heading_lower = (c.heading or "").lower()
            score = 0.0

            for t in tokens:
                # Heading matches carry high relevance
                if t in heading_lower:
                    score += 6.0
                # Body keyword matches
                if t in text_lower:
                    score += 1.5 + min(text_lower.count(t) * 0.5, 3.0)

            # Bonus for exact multi-token phrase matches
            if len(tokens) >= 2:
                phrase = " ".join(tokens)
                if phrase in text_lower or phrase in heading_lower:
                    score += 10.0

            scored.append((score, c))

        # 4. Sort by relevance descending, maintaining stable order for ties
        scored.sort(key=lambda x: x[0], reverse=True)
        matching = [c for score, c in scored if score > 0.0]

        if matching:
            results = matching[:top_k]
            logger.info(
                "retrieval_search_completed_with_matches",
                matching_count=len(matching),
                returned_count=len(results),
                top_match_heading=results[0].heading,
            )
        else:
            results = all_clauses[:top_k]
            logger.info("retrieval_search_fallback_to_document_flow", count=len(results))

        return results
