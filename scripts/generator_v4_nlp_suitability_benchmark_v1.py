"""GEN-010.11 text-only NLP suitability benchmark.

The predictor receives only rendered body text. Event labels and contact IDs are
joined only after prediction by the evaluator. Organization-held-out evaluation
prevents same-organization record leakage across the evaluation boundary.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from typing import Any

from generator_v4_scenario_engine_v1 import build
from generator_v4_communication_renderer_v1 import render_communications
from generator_v4_composite_bpmn_audit_v1 import CONFIG

# Ordered, interpretable lexical baseline. This is a diagnostic baseline, not a trained model.
RULES = [
    ("close", ("эпизод", "закрыт", "закрытие процесса", "завершает последовательность")),
    ("reject", ("отклон", "отказ", "отрицательн")),
    ("approve", ("одобр", "положительное итоговое решение", "итоговое согласование")),
    ("unit_approval", ("согласование подраздел", "профильное согласование", "область ответственности подразделения")),
    ("object", ("возраж", "замечан", "несоглас", "не поддерживаю")),
    ("revise", ("доработ", "коррект", "обновлён", "обновлен", "изменён", "изменен", "повторн")),
    ("delegate", ("поручен", "назнач", "передаётся на экспертную", "передается на экспертную")),
    ("complete_task", ("выполнен", "завершение порученной", "проверка выполнена", "статус задачи")),
    ("recommend", ("рекомендац", "экспертный вывод", "заключение", "экспертную позицию")),
    ("review", ("рассмотр", "обсужден", "обсуждени", "протокол", "встреча посвящена")),
    ("request_information", ("запрашиваются исходные", "прошу предоставить", "исходную информацию", "исходные сведения", "запрос")),
]
LABELS = tuple(label for label, _ in RULES)


def predict_event_type(text: str) -> str:
    value = (text or "").lower()
    for label, markers in RULES:
        if any(marker in value for marker in markers):
            return label
    return "abstain"


def _f1(tp: int, fp: int, fn: int) -> float:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def run_benchmark(world: dict[str, Any], communications: list[dict[str, Any]]) -> dict[str, Any]:
    org_ids = sorted({row["organization_id"] for row in communications})
    held_out = set(org_ids[-4:])
    predictions = []
    errors = []
    confusion = Counter()
    by_label = defaultdict(lambda: Counter())
    binary = {
        "objection": {"positive": {"object"}, "tp": 0, "fp": 0, "fn": 0},
        "revision": {"positive": {"revise"}, "tp": 0, "fp": 0, "fn": 0},
        "recommendation": {"positive": {"recommend"}, "tp": 0, "fp": 0, "fn": 0},
        "final_decision": {"positive": {"approve", "reject"}, "tp": 0, "fp": 0, "fn": 0},
    }

    for row in communications:
        # The model-facing prediction function receives only body text.
        predicted = predict_event_type(row.get("body", ""))
        actual = row["event_type"]  # evaluator-only label, joined after prediction
        split = "held_out_org" if row["organization_id"] in held_out else "development_org"
        confusion[(actual, predicted)] += 1
        by_label[actual]["total"] += 1
        by_label[actual]["correct"] += int(actual == predicted)
        if predicted == "abstain":
            by_label[actual]["abstain"] += 1
        predictions.append({"source_event_id": row["source_event_id"],
                            "organization_id": row["organization_id"],
                            "split": split, "predicted_event_type": predicted})
        for task in binary.values():
            expected = actual in task["positive"]
            observed = predicted in task["positive"]
            if expected and observed:
                task["tp"] += 1
            elif not expected and observed:
                task["fp"] += 1
            elif expected and not observed:
                task["fn"] += 1

        # Attribution must abstain when it cannot be inferred from the body.
        # The current renderer's body is not allowed to smuggle contact IDs into this task.
        if re.search(r"\\b(?:ORG-\\d+|C\\d+)\\b", row.get("body", "")):
            errors.append("contact identifier leaked into body " + row["source_event_id"])

    held = [p for p in predictions if p["split"] == "held_out_org"]
    dev = [p for p in predictions if p["split"] == "development_org"]
    held_correct = sum(p["predicted_event_type"] == next(
        r["event_type"] for r in communications if r["source_event_id"] == p["source_event_id"]
    ) for p in held)
    dev_correct = sum(p["predicted_event_type"] == next(
        r["event_type"] for r in communications if r["source_event_id"] == p["source_event_id"]
    ) for p in dev)
    total = len(predictions)
    correct = sum(v for (actual, predicted), v in confusion.items() if actual == predicted)
    per_class = {}
    macro_f1_values = []
    for label in sorted({actual for actual, _ in confusion}):
        tp = confusion[(label, label)]
        fp = sum(v for (actual, predicted), v in confusion.items() if predicted == label and actual != label)
        fn = sum(v for (actual, predicted), v in confusion.items() if actual == label and predicted != label)
        f1 = _f1(tp, fp, fn)
        macro_f1_values.append(f1)
        per_class[label] = {"support": sum(v for (actual, _), v in confusion.items() if actual == label),
                            "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
                            "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
                            "f1": round(f1, 4)}
    binary_report = {}
    for name, task in binary.items():
        tp, fp, fn = task["tp"], task["fp"], task["fn"]
        binary_report[name] = {"precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
                               "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
                               "f1": round(_f1(tp, fp, fn), 4),
                               "tp": tp, "fp": fp, "fn": fn}

    # No person-level author/executor/decision-maker is inferable from this text-only baseline.
    attribution = {
        "task": "person_identity_from_body_only",
        "predicted_person_ids": 0,
        "abstained_records": total,
        "verified_person_identity_claims": 0,
        "status": "SAFE_ABSTENTION",
        "reason": "Rendered body text does not contain verified turn-level speaker identity; structured CRM metadata is not NLP evidence."
    }
    return {
        "audit": "GEN-010.11",
        "status": "PASS" if total == len(world["observable_events"]) and not errors else "FAIL",
        "benchmark_mode": "interpretable_lexical_baseline_not_trained_model",
        "model_input": "body_text_only",
        "evaluation_labels_joined_after_prediction": True,
        "split_strategy": "organization_group_holdout",
        "development_organizations": sorted(set(org_ids) - held_out),
        "held_out_organizations": sorted(held_out),
        "communications": total,
        "unique_source_events": len({p["source_event_id"] for p in predictions}),
        "event_type_classification": {
            "accuracy": round(correct / total, 4) if total else 0.0,
            "macro_f1": round(sum(macro_f1_values) / len(macro_f1_values), 4) if macro_f1_values else 0.0,
            "development_accuracy": round(dev_correct / len(dev), 4) if dev else 0.0,
            "held_out_accuracy": round(held_correct / len(held), 4) if held else 0.0,
            "per_class": per_class,
            "confusion_matrix": {actual: {predicted: count for (a, predicted), count in confusion.items() if a == actual}
                                 for actual in sorted({a for a, _ in confusion})},
        },
        "binary_event_tasks": binary_report,
        "person_attribution": attribution,
        "known_limitations": [
            "A lexical baseline is a smoke test, not evidence of generalization by a learned NLP model.",
            "Synthetic renderer phrases can be easier to classify than natural CRM messages.",
            "The 20-organization holdout is small; external and human-reviewed data are still required.",
            "Speaker identity is not recoverable from current body text; abstention is the correct outcome.",
            "Chronology is available in structured event timestamps, not reconstructed from free text."
        ],
        "errors": errors,
    }


def main():
    world = build(config=CONFIG)
    communications = render_communications(
        world["observable_events"], world["organizations"], world["seed"]
    )
    report = run_benchmark(world, communications)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
