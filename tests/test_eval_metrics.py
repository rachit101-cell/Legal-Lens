"""
LegalLens — Unit Tests for Evaluation Metrics.

Tests precision, recall, F1, taxonomy classification accuracy, macro-F1,
and attention findings detection & calibration scoring.
"""

from __future__ import annotations

from tests.eval_metrics import (
    calculate_precision_recall,
    evaluate_findings,
    evaluate_taxonomy,
)


def test_calculate_precision_recall_identical():
    """Identical sets should yield 1.0 for precision, recall, and F1."""
    expected = {"clause_1", "clause_2", "clause_3"}
    actual = {"clause_1", "clause_2", "clause_3"}
    p, r, f1 = calculate_precision_recall(expected, actual)
    assert p == 1.0
    assert r == 1.0
    assert f1 == 1.0


def test_calculate_precision_recall_disjoint():
    """Completely disjoint sets should yield 0.0."""
    expected = {"clause_1", "clause_2"}
    actual = {"clause_3", "clause_4"}
    p, r, f1 = calculate_precision_recall(expected, actual)
    assert p == 0.0
    assert r == 0.0
    assert f1 == 0.0


def test_calculate_precision_recall_empty():
    """Empty sets should handle edge cases safely."""
    p, r, f1 = calculate_precision_recall(set(), set())
    assert p == 1.0
    assert r == 1.0
    assert f1 == 1.0

    p, r, f1 = calculate_precision_recall({"a"}, set())
    assert p == 0.0
    assert r == 0.0
    assert f1 == 0.0


def test_calculate_precision_recall_partial():
    """Partial overlap should compute correct harmonic mean."""
    expected = {"a", "b", "c", "d"}
    actual = {"a", "b", "e"}
    # TP = 2, FP = 1, FN = 2
    # Precision = 2/3 = 0.6667
    # Recall = 2/4 = 0.5
    # F1 = 2 * (2/3 * 0.5) / (2/3 + 0.5) = 2/3 / (7/6) = 4/7 = 0.5714
    p, r, f1 = calculate_precision_recall(expected, actual)
    assert p == 0.6667
    assert r == 0.5
    assert f1 == 0.5714


def test_evaluate_taxonomy_all_correct():
    """When all clauses match expected taxonomy, accuracy and macro F1 are 1.0."""
    expected = {
        "c1": "CONFIDENTIALITY_IP",
        "c2": "TERM_RENEWAL",
        "c3": "DISPUTE_GOVERNING_LAW",
    }
    actual = {
        "c1": "CONFIDENTIALITY_IP",
        "c2": "TERM_RENEWAL",
        "c3": "DISPUTE_GOVERNING_LAW",
    }
    res = evaluate_taxonomy("doc_1", expected, actual)
    assert res["accuracy"] == 1.0
    assert res["macro_f1"] == 1.0
    assert res["correct_matches"] == 3
    assert len(res["misclassifications"]) == 0


def test_evaluate_taxonomy_with_misclassifications():
    """Misclassified clauses should be recorded and affect metrics correctly."""
    expected = {
        "c1": "CONFIDENTIALITY_IP",
        "c2": "TERM_RENEWAL",
        "c3": "LIABILITY_INDEMNITY",
    }
    actual = {
        "c1": "CONFIDENTIALITY_IP",
        "c2": "BOILERPLATE",  # Mismatch
        "c3": "LIABILITY_INDEMNITY",
    }
    res = evaluate_taxonomy("doc_2", expected, actual)
    assert res["correct_matches"] == 2
    assert res["total_clauses"] == 3
    assert res["accuracy"] == round(2 / 3, 4)
    assert len(res["misclassifications"]) == 1
    assert res["misclassifications"][0]["clause_id"] == "c2"
    assert res["misclassifications"][0]["expected"] == "TERM_RENEWAL"
    assert res["misclassifications"][0]["actual"] == "BOILERPLATE"


def test_evaluate_findings():
    """Finding evaluation should check detection, severity match, and citations."""
    expected_findings = [
        {
            "category": "LIABILITY",
            "severity": "IMPORTANT",
            "clause_id": "c_liab",
        },
        {
            "category": "TERMINATION",
            "severity": "NEEDS_REVIEW",
            "clause_id": "c_term",
        },
    ]

    actual_findings = [
        {
            "category": "LIABILITY",
            "severity": "IMPORTANT",
            "clause_id": "c_liab",
            "evidence_quote": "Liability shall not exceed $2,000,000",
        },
        {
            "category": "TERMINATION",
            "severity": "NEEDS_REVIEW",
            "clause_id": "c_term",
            "evidence_quote": "30 days notice required",
        },
    ]

    res = evaluate_findings("doc_test", expected_findings, actual_findings)
    assert res["precision"] == 1.0
    assert res["recall"] == 1.0
    assert res["f1"] == 1.0
    assert res["severity_accuracy"] == 1.0
    assert res["citation_grounding_score"] == 1.0
    assert res["overall_alignment_score"] == 100.0
