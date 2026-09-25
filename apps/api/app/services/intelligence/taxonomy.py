"""
LegalLens API — Taxonomy Classification Service.

Classifies clauses into standard legal taxonomy categories.
"""

from __future__ import annotations

from typing import Sequence

import structlog

from app.models.analysis import Clause

logger = structlog.get_logger()

# Naive taxonomy rules mapping keywords to classes
TAXONOMY_RULES = {
    "Liability": ["liability", "indemnify", "indemnification", "damages", "hold harmless"],
    "Termination": ["terminate", "termination", "expire", "expiration", "survival"],
    "Confidentiality": ["confidential", "confidentiality", "non-disclosure", "trade secret"],
    "Governing Law": ["governing law", "jurisdiction", "venue", "courts of"],
    "Payment": ["payment", "fee", "invoice", "taxes", "compensation"],
    "Warranties": ["warranty", "warranties", "merchantability", "fitness for a particular purpose", "as is"],
}


class TaxonomyService:
    """Service to classify clauses into a legal taxonomy."""

    def classify_clauses(self, clauses: Sequence[Clause]) -> None:
        """
        Scan clauses and assign a taxonomy_class based on heuristic rules.
        Modifies the clauses in-place.
        """
        for clause in clauses:
            text = clause.text.lower()
            assigned_class = None
            
            # Simple keyword matching
            for tax_class, keywords in TAXONOMY_RULES.items():
                if any(kw in text for kw in keywords):
                    assigned_class = tax_class
                    break
                    
            if assigned_class:
                clause.taxonomy_class = assigned_class
                
        logger.info("taxonomy_classification_complete", count=len(clauses))
