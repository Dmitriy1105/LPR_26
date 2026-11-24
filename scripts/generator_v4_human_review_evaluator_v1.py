"""GEN-010.11B reviewer agreement and adjudication evaluator.

Input files are independent reviewer annotations, an adjudicated annotation file,
and a restricted Ground Truth answer key. The answer key is read only after the
reviewer annotations are locked. No labels are inferred or fabricated here.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

EVENT_TYPES = (
    "request_information", "delegate", "complete_task", "review", "recommend",
    "object", "revise", "unit_approval", "approve", "reject", "close", "unclear"
)
RATINGS = ("event_clarity_1_to_5", "naturalness_1_to_5", "factual_support_1_to_5")


def load_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _annotation_map(payload: dict[str, Any], reviewer: str) -> dict[str, dict[str, Any]]:
    rows = payload.get("records")
    if not isinstance(rows, list):
        raise ValueError(f"{reviewer}: records must be a list")
    result = {}
    for row in rows:
        rid = row.get("review_id")
        if not rid or rid in result:
            raise ValueError(f"{reviewer}: missing or duplicate review_id {rid!r}")
        result[rid] = row
    return result


def _validate_labels(rows: dict[str, dict[str, Any]], reviewer: str, expected_ids: set[str]):
    if set(rows) != expected_ids:
        raise ValueError(
            f"{reviewer}: review_id coverage mismatch; "
            f"missing={len(expected_ids-set(rows))}, extra={len(set(rows)-expected_ids)}"
        )
    for rid, row in rows.items():
        label = row.get("primary_event_type")
        if label not in EVENT_TYPES:
            raise ValueError(f"{reviewer}: invalid or missing primary_event_type for {rid}: {label!r}")
        for field in RATINGS:
            value = row.get(field)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5):
                raise ValueError(f"{reviewer}: {field} must be integer 1..5 or null for {rid}")
        if not isinstance(row.get("unsupported_claims", []), list):
            raise ValueError(f"{reviewer}: unsupported_claims must be a list for {rid}")


def _kappa(labels_a: list[str], labels_b: list[str]) -> dict[str, Any]:
    if len(labels_a) != len(labels_b) or not labels_a:
        raise ValueError("Cohen kappa requires equally sized non-empty label arrays")
    n = len(labels_a)
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / n
    categories = sorted(set(labels_a) | set(labels_b))
    ca, cb = Counter(labels_a), Counter(labels_b)
    expected = sum((ca[c] / n) * (cb[c] / n) for c in categories)
    kappa = (observed - expected) / (1 - expected) if expected != 1 else (1.0 if observed == 1 else 0.0)
    return {
        "n": n,
        "raw_agreement": round(observed, 4),
        "cohen_kappa": round(kappa, 4),
        "expected_agreement_by_chance": round(expected, 4),
        "categories": categories,
        "interpretation_note": "Kappa is prevalence-sensitive; report alongside raw agreement and class distribution."
    }


def _classification_metrics(actual: list[str], predicted: list[str]) -> dict[str, Any]:
    matrix = {label: {pred: 0 for pred in EVENT_TYPES} for label in EVENT_TYPES}
    for a, p in zip(actual, predicted):
        matrix[a][p] += 1
    per_class = {}
    f1s = []
    for label in EVENT_TYPES:
        tp = matrix[label][label]
        fp = sum(matrix[a][label] for a in EVENT_TYPES if a != label)
        fn = sum(matrix[label][p] for p in EVENT_TYPES if p != label)
        support = sum(matrix[label].values())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {
            "support": support, "precision": round(precision, 4),
            "recall": round(recall, 4), "f1": round(f1, 4)
        }
        f1s.append(f1)
    total = len(actual)
    accuracy = sum(a == p for a, p in zip(actual, predicted)) / total if total else 0.0
    return {
        "n": total,
        "accuracy": round(accuracy, 4),
        "macro_f1_all_12_labels": round(mean(f1s), 4),
        "per_class": per_class,
        "confusion_matrix_actual_rows_predicted_columns": matrix
    }


def _rating_summary(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    output = {}
    for field in RATINGS:
        values = [row[field] for row in rows.values() if row.get(field) is not None]
        output[field] = {
            "n": len(values),
            "mean": round(mean(values), 3) if values else None,
            "median": median(values) if values else None,
            "distribution": dict(sorted(Counter(values).items()))
        }
    unsupported = sum(bool(row.get("unsupported_claims")) for row in rows.values())
    total = len(rows)
    return {
        "ratings": output,
        "records_with_unsupported_claims": unsupported,
        "unsupported_claim_rate": round(unsupported / total, 4) if total else 0.0,
        "unsupported_claim_items": sum(len(row.get("unsupported_claims", [])) for row in rows.values())
    }


def evaluate(reviewer1: dict, reviewer2: dict, adjudicated: dict, answer_key: dict) -> dict[str, Any]:
    r1 = _annotation_map(reviewer1, "reviewer_1")
    r2 = _annotation_map(reviewer2, "reviewer_2")
    adj = _annotation_map(adjudicated, "adjudicated")
    key_rows = answer_key.get("records")
    if not isinstance(key_rows, list):
        raise ValueError("answer key records must be a list")
    key = {}
    for row in key_rows:
        rid = row.get("review_id")
        if not rid or rid in key:
            raise ValueError(f"answer key missing or duplicate review_id {rid!r}")
        key[rid] = row
    expected_ids = set(key)
    if len(expected_ids) != 220:
        raise ValueError(f"expected 220 answer-key records, got {len(expected_ids)}")
    for name, rows in (("reviewer_1", r1), ("reviewer_2", r2), ("adjudicated", adj)):
        _validate_labels(rows, name, expected_ids)

    ids = sorted(expected_ids)
    labels1 = [r1[rid]["primary_event_type"] for rid in ids]
    labels2 = [r2[rid]["primary_event_type"] for rid in ids]
    labels_adj = [adj[rid]["primary_event_type"] for rid in ids]
    gold = [key[rid]["ground_truth_event_type"] for rid in ids]
    if any(label not in EVENT_TYPES[:-1] for label in gold):
        raise ValueError("answer key contains an unknown ground-truth event class")

    by_channel = defaultdict(lambda: {"r1": [], "r2": []})
    disagreements = []
    for rid in ids:
        channel = key[rid].get("channel", "unknown")
        by_channel[channel]["r1"].append(r1[rid]["primary_event_type"])
        by_channel[channel]["r2"].append(r2[rid]["primary_event_type"])
        if r1[rid]["primary_event_type"] != r2[rid]["primary_event_type"]:
            disagreements.append({
                "review_id": rid,
                "reviewer_1": r1[rid]["primary_event_type"],
                "reviewer_2": r2[rid]["primary_event_type"],
                "adjudicated": adj[rid]["primary_event_type"],
                "adjudication_reason": adj[rid].get("reason", "")
            })

    channel_agreement = {}
    for channel, vals in sorted(by_channel.items()):
        channel_agreement[channel] = _kappa(vals["r1"], vals["r2"])

    return {
        "audit": "GEN-010.11B",
        "status": "PASS",
        "records": len(ids),
        "reviewer_agreement": _kappa(labels1, labels2),
        "agreement_by_channel": channel_agreement,
        "disagreements": {
            "count": len(disagreements),
            "rate": round(len(disagreements) / len(ids), 4),
            "adjudicated_examples": disagreements
        },
        "adjudication_vs_ground_truth": _classification_metrics(gold, labels_adj),
        "reviewer_1_ratings_and_claims": _rating_summary(r1),
        "reviewer_2_ratings_and_claims": _rating_summary(r2),
        "adjudication_coverage": {
            "records_with_reason": sum(bool(adj[rid].get("reason", "").strip()) for rid in ids),
            "disagreements": len(disagreements)
        },
        "limitations": [
            "Cohen kappa is reported with raw agreement because class prevalence affects kappa.",
            "The 220-record sample is balanced by design and is not prevalence-representative of the full corpus.",
            "Agreement with synthetic Ground Truth measures consistency with the scenario contract, not truth about real customers.",
            "Human ratings are subjective and require documented reviewer qualifications and adjudication."
        ]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer1", required=True)
    parser.add_argument("--reviewer2", required=True)
    parser.add_argument("--adjudicated", required=True)
    parser.add_argument("--answer-key", required=True,
                        help="Restricted file; use only after both reviewer files are locked.")
    parser.add_argument("--output", default="gen01011b-human-evaluation-report.json")
    args = parser.parse_args()
    report = evaluate(
        load_json(args.reviewer1), load_json(args.reviewer2),
        load_json(args.adjudicated), load_json(args.answer_key)
    )
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "records": report["records"],
                      "agreement": report["reviewer_agreement"],
                      "adjudicated_accuracy": report["adjudication_vs_ground_truth"]["accuracy"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
