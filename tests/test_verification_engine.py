"""
LegalLens — Unit Tests for Dual-Stage Verification Engine.

Tests strict refusal guarantees, hallucination detection, citation checking,
and evidence grounding.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.services.evidence.verification_engine import VerificationEngine
from packages.schemas.enums import SupportStatus


def test_verification_empty_evidence_refusal():
    """Engine must strictly refuse claims when no evidence is cited."""
    engine = VerificationEngine()
    status, notes = engine.verify_claim("This contract requires 30 days notice.", [])
    assert status == SupportStatus.UNSUPPORTED
    assert "No evidence" in notes


def test_verification_supported_claim():
    """Engine must verify claims whose terminology is grounded in cited text."""
    engine = VerificationEngine()
    mock_clause = MagicMock()
    mock_clause.original_text = "Either party may terminate this agreement upon thirty (30) days written notice."

    status, notes = engine.verify_claim(
        "Either party may terminate upon thirty days written notice.",
        [mock_clause],
    )
    assert status == SupportStatus.SUPPORTED
    assert "supported" in notes.lower()


def test_verification_hallucination_flagged():
    """Engine must flag claims with extraneous/invented obligations."""
    engine = VerificationEngine()
    mock_clause = MagicMock()
    mock_clause.original_text = "This contract is governed by the laws of Delaware."

    # Claim talks about non-existent arbitration in Tokyo with 5 million dollar damages
    hallucinated_claim = "All disputes must be submitted to binding arbitration in Tokyo Japan with liquidated damages of five million dollars."
    status, notes = engine.verify_claim(hallucinated_claim, [mock_clause])

    assert status == SupportStatus.UNSUPPORTED
    assert "absent" in notes.lower() or "unsupported" in notes.lower()
