"""
LegalLens — Evaluation Metrics.

Defines the core metrics used to evaluate the pipeline against the golden dataset:
1. Precision, Recall, and F1 Score calculation.
2. Taxonomy classification accuracy, macro-F1, and per-class breakdown.
3. Attention findings detection, severity calibration, and citation grounding metrics.
"""

from __future__ import annotations

from typing import Any


def calculate_precision_recall(expected: set[Any], actual: set[Any]) -> tuple[float, float, float]:
    """
    Calculate Precision, Recall, and F1 Score for extracted sets.

    Returns:
        tuple[float, float, float]: (precision, recall, f1_score) in [0.0, 1.0].
    """
    if not expected and not actual:
        return 1.0, 1.0, 1.0

    true_positives = len(expected.intersection(actual))
    false_positives = len(actual - expected)
    false_negatives = len(expected - actual)

    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0.0
    )

    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return round(precision, 4), round(recall, 4), round(f1, 4)


def evaluate_taxonomy(
    document_id: str,
    expected_classes: dict[str, str],
    actual_classes: dict[str, str],
) -> dict[str, Any]:
    """
    Evaluate if clauses were classified with the correct taxonomy labels.

    Args:
        document_id: Identifier of the document being evaluated.
        expected_classes: Mapping of clause_id -> expected taxonomy label.
        actual_classes: Mapping of clause_id -> actual predicted taxonomy label.

    Returns:
        dict: Detailed metrics including accuracy, macro_f1, per_class metrics, and misclassifications.
    """
    if not expected_classes:
        return {
            "document_id": document_id,
            "total_clauses": 0,
            "accuracy": 1.0,
            "macro_f1": 1.0,
            "per_class": {},
            "misclassifications": [],
        }

    total_clauses = len(expected_classes)
    correct_matches = 0
    misclassifications: list[dict[str, str]] = []

    # Track per-class True Positives, False Positives, False Negatives
    all_classes = set(expected_classes.values()).union(set(actual_classes.values()))
    class_stats: dict[str, dict[str, int]] = {
        cls_name: {"tp": 0, "fp": 0, "fn": 0} for cls_name in all_classes
    }

    for clause_id, exp_cls in expected_classes.items():
        act_cls = actual_classes.get(clause_id, "UNKNOWN")
        if exp_cls == act_cls:
            correct_matches += 1
            class_stats[exp_cls]["tp"] += 1
        else:
            class_stats[exp_cls]["fn"] += 1
            if act_cls in class_stats:
                class_stats[act_cls]["fp"] += 1
            misclassifications.append({
                "clause_id": clause_id,
                "expected": exp_cls,
                "actual": act_cls,
            })

    accuracy = correct_matches / total_clauses if total_clauses > 0 else 0.0

    # Calculate per-class Precision, Recall, F1 and macro average
    per_class_metrics: dict[str, dict[str, float]] = {}
    f1_scores: list[float] = []

    for cls_name, stats in class_stats.items():
        tp = stats["tp"]
        fp = stats["fp"]
        fn = stats["fn"]

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        if (tp + fn) > 0:  # Only include classes that were expected in macro avg
            f1_scores.append(f1)

        per_class_metrics[cls_name] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": tp + fn,
        }

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

    return {
        "document_id": document_id,
        "total_clauses": total_clauses,
        "correct_matches": correct_matches,
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class_metrics,
        "misclassifications": misclassifications,
    }


def evaluate_findings(
    document_id: str,
    expected_findings: list[dict[str, Any]],
    actual_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Evaluate if the heuristic and LLM findings correctly identified risks,
    including severity calibration and evidence citation completeness.

    Args:
        document_id: Identifier of the document evaluated.
        expected_findings: List of expected finding dicts (category, severity, optional clause_id).
        actual_findings: List of actual detected finding dicts.

    Returns:
        dict: Evaluation results including detection precision/recall/F1, severity match rate,
              and citation grounding score.
    """
    # Key findings by category + clause if available, otherwise by category
    def finding_key(f: dict[str, Any]) -> tuple[str, str]:
        category = str(f.get("category", "")).upper()
        clause_id = str(f.get("clause_id", f.get("source_clause_id", "")))
        return category, clause_id

    expected_keys = {finding_key(f) for f in expected_findings}
    actual_keys = {finding_key(f) for f in actual_findings}

    precision, recall, f1 = calculate_precision_recall(expected_keys, actual_keys)

    # Severity calibration check for matched findings
    actual_map = {finding_key(f): f for f in actual_findings}
    matched_count = 0
    severity_matches = 0
    grounded_citations = 0

    for exp in expected_findings:
        k = finding_key(exp)
        if k in actual_map:
            matched_count += 1
            act = actual_map[k]
            # Severity check
            if str(exp.get("severity", "")).upper() == str(act.get("severity", "")).upper():
                severity_matches += 1
            # Grounding check (must have evidence quote or citation link)
            has_evidence = bool(
                act.get("evidence_quote")
                or act.get("clause_id")
                or act.get("source_clause_id")
                or act.get("citations")
            )
            if has_evidence:
                grounded_citations += 1

    severity_accuracy = (severity_matches / matched_count) if matched_count > 0 else 1.0
    grounding_score = (grounded_citations / len(actual_findings)) if actual_findings else 1.0

    return {
        "document_id": document_id,
        "expected_count": len(expected_findings),
        "actual_count": len(actual_findings),
        "matched_count": matched_count,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "severity_accuracy": round(severity_accuracy, 4),
        "citation_grounding_score": round(grounding_score, 4),
        "overall_alignment_score": round((f1 * 0.5 + severity_accuracy * 0.25 + grounding_score * 0.25) * 100, 2),
    }
