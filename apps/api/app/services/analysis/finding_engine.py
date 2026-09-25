"""
LegalLens API — Finding Engine.

Runs detectors over extracted clauses and entities to identify risks,
anomalies, or missing information.
"""

from __future__ import annotations

from typing import Sequence

import structlog

from app.models.analysis import Clause, Entity, Finding
from app.models.base import generate_prefixed_uuid

logger = structlog.get_logger()


class FindingEngine:
    """Service to run analytical detectors and generate Findings."""

    def generate_findings(
        self, 
        document_id: str, 
        analysis_id: str, 
        clauses: Sequence[Clause],
        entities: Sequence[Entity],
    ) -> list[Finding]:
        """
        Run heuristic rules over clauses and entities.
        """
        findings: list[Finding] = []
        
        has_termination = False
        has_governing_law = False

        for clause in clauses:
            if clause.taxonomy_class == "Termination":
                has_termination = True
            elif clause.taxonomy_class == "Governing Law":
                has_governing_law = True
                
        # Detector 1: Missing Termination Clause
        if not has_termination:
            findings.append(
                Finding(
                    id=generate_prefixed_uuid("fnd"),
                    analysis_id=analysis_id,
                    document_id=document_id,
                    finding_type="MISSING_CLAUSE",
                    severity="HIGH",
                    description="The document does not appear to contain a termination clause.",
                    recommendation="Review the document for any implied termination rights or add a standard termination for convenience clause.",
                    clause_ids=[],
                )
            )
            
        # Detector 2: Missing Governing Law
        if not has_governing_law:
            findings.append(
                Finding(
                    id=generate_prefixed_uuid("fnd"),
                    analysis_id=analysis_id,
                    document_id=document_id,
                    finding_type="MISSING_CLAUSE",
                    severity="MEDIUM",
                    description="No governing law or jurisdiction clause detected.",
                    recommendation="Specify the applicable governing law to avoid jurisdictional disputes.",
                    clause_ids=[],
                )
            )

        # Detector 3: High Liability Amounts
        for entity in entities:
            if entity.entity_type == "MONEY":
                # Naive parse to check if amount > 1M
                # strip non-numeric except decimal
                try:
                    num_str = "".join(c for c in entity.value if c.isdigit() or c == ".")
                    if num_str and float(num_str) > 1000000:
                        findings.append(
                            Finding(
                                id=generate_prefixed_uuid("fnd"),
                                analysis_id=analysis_id,
                                document_id=document_id,
                                finding_type="RISK",
                                severity="HIGH",
                                description=f"High monetary exposure detected: {entity.value}",
                                recommendation="Review the associated clause to ensure appropriate liability caps or approvals are in place.",
                                clause_ids=[entity.clause_id] if entity.clause_id else [],
                            )
                        )
                except Exception:
                    pass

        logger.info(
            "finding_generation_complete",
            document_id=document_id,
            finding_count=len(findings),
        )
        return findings
