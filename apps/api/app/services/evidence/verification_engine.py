"""
LegalLens API — Verification Engine.

Independently verifies claims made by the generative AI layer against the
cited source clauses to detect and flag hallucinations.
"""

from __future__ import annotations

import structlog

from app.models.analysis import Clause
from packages.schemas.enums import SupportStatus

# In a real system, we'd use a small, focused LLM or NLI model here
# to check entailment (Does Premise [Clause] entail Hypothesis [Claim]?).
# from transformers import pipeline

logger = structlog.get_logger()


class VerificationEngine:
    """Service to classify and verify claims against evidence."""

    def __init__(self) -> None:
        # e.g., self.nli_model = pipeline("zero-shot-classification", model="roberta-large-mnli")
        pass

    def verify_claim(self, claim_text: str, evidence_clauses: list[Clause]) -> tuple[SupportStatus, str]:
        """
        Check if the claim_text is supported by the evidence_clauses.
        Returns a tuple of (SupportStatus, VerificationNotes).
        """
        logger.info("verifying_claim", claim=claim_text, evidence_count=len(evidence_clauses))
        
        if not evidence_clauses:
            return SupportStatus.UNSUPPORTED, "No evidence provided to support the claim."
            
        combined_evidence = " ".join([c.original_text for c in evidence_clauses])
        
        # Stub implementation for MVP
        # In a real app, this would use NLI (Natural Language Inference) to check entailment.
        # If the claim contains words that are totally absent from evidence, we could flag it.
        
        # Extremely naive heuristic stub:
        claim_words = set(claim_text.lower().split())
        evidence_words = set(combined_evidence.lower().split())
        
        # If too many words in the claim are novel, maybe it's hallucinated?
        novel_words = claim_words - evidence_words
        
        if len(novel_words) > len(claim_words) * 0.5:
            # More than 50% of the claim words don't appear in the evidence
            return SupportStatus.UNSUPPORTED, "Significant portion of claim terminology is absent from source."
            
        return SupportStatus.SUPPORTED, "Claim appears supported by cited text."

verification_engine = VerificationEngine()
