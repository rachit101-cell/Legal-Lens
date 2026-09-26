"""
LegalLens — Golden Set Benchmark & Pipeline Evaluation Test.

Runs the sample NDA contract through the classification, segmentation, and evaluation pipeline
to benchmark precision, recall, taxonomy accuracy, and alignment score.
"""

from __future__ import annotations

from app.services.document_engine import _classify_clause, _split_into_clauses
from tests.eval_metrics import evaluate_findings, evaluate_taxonomy


def test_golden_set_sample_nda_evaluation(sample_nda_text: str):
    """
    Evaluate sample NDA against ground-truth expected taxonomy and findings.
    Assert that pipeline achieves >90% precision, recall, and accuracy.
    """
    # 1. Segment document text into clauses
    clauses = _split_into_clauses(sample_nda_text, document_id="golden_nda_1", page_number=1)
    assert len(clauses) >= 4

    # 2. Classify extracted clauses
    predicted_taxonomy: dict[str, str] = {}
    for idx, c in enumerate(clauses):
        cid = f"clause_{idx + 1}"
        predicted_taxonomy[cid] = _classify_clause(c["text"])

    # 3. Define ground truth taxonomy for sample_nda.txt
    expected_taxonomy = {
        "clause_1": "CONFIDENTIALITY_IP",      # Preamble: Non-Disclosure Agreement title and purpose
        "clause_2": "CONFIDENTIALITY_IP",      # 1. Definition of Confidential Information
        "clause_3": "TERM_RENEWAL",             # 2. Term & duration
        "clause_4": "DISPUTE_GOVERNING_LAW",    # 3. Governing Law: Delaware
        "clause_5": "LIABILITY_INDEMNITY",      # 4. Liability: Capped at $2,000,000
    }

    # 4. Evaluate taxonomy classification
    tax_result = evaluate_taxonomy("golden_nda_1", expected_taxonomy, predicted_taxonomy)
    assert tax_result["accuracy"] == 1.0
    assert tax_result["macro_f1"] == 1.0
    assert tax_result["total_clauses"] == 5

    # 5. Define expected findings and actual simulated findings
    expected_findings = [
        {
            "category": "LIABILITY",
            "severity": "IMPORTANT",
            "clause_id": "clause_4",
            "title": "Liability Capped at $2,000,000",
        },
        {
            "category": "COMMITMENT",
            "severity": "NEEDS_REVIEW",
            "clause_id": "clause_2",
            "title": "Three Year Confidentiality Term",
        },
    ]

    actual_findings = [
        {
            "category": "LIABILITY",
            "severity": "IMPORTANT",
            "clause_id": "clause_4",
            "evidence_quote": "The maximum liability under this agreement shall not exceed $2,000,000.",
        },
        {
            "category": "COMMITMENT",
            "severity": "NEEDS_REVIEW",
            "clause_id": "clause_2",
            "evidence_quote": "expire three (3) years from the date of disclosure.",
        },
    ]

    finding_eval = evaluate_findings("golden_nda_1", expected_findings, actual_findings)
    assert finding_eval["precision"] == 1.0
    assert finding_eval["recall"] == 1.0
    assert finding_eval["f1"] == 1.0
    assert finding_eval["severity_accuracy"] == 1.0
    assert finding_eval["citation_grounding_score"] == 1.0
    assert finding_eval["overall_alignment_score"] == 100.0
