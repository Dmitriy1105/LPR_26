"""GEN-010.9 renderer QC and lexical diversity diagnostic; in-memory only."""
import json
import re
from collections import Counter, defaultdict
from itertools import combinations

from generator_v4_scenario_engine_v1 import build
from generator_v4_composite_bpmn_audit_v1 import CONFIG
from generator_v4_communication_renderer_v1 import (
    render_communications, validate_rendered_communications
)


def normalize(text):
    value = text.lower()
    value = re.sub(r"org-\d+-d\d+-e\d+|org-\d+-d\d+|comm:org-\d+-d\d+-e\d+", " ", value)
    value = re.sub(r"\b\d+\b", " ", value)
    return re.sub(r"[^\wа-яё]+", " ", value, flags=re.IGNORECASE).strip()


def jaccard(left, right):
    a, b = set(normalize(left).split()), set(normalize(right).split())
    return len(a & b) / len(a | b) if a or b else 1.0


def audit():
    world = build(config=CONFIG)
    communications = render_communications(
        world["observable_events"], world["organizations"], world["seed"]
    )
    validation = validate_rendered_communications(world["observable_events"], communications)
    channels = dict(Counter(row["channel"] for row in communications))
    event_types = dict(Counter(row["event_type"] for row in communications))
    missing = sum(bool(row["missing_fields"]) for row in communications)

    grouped = defaultdict(list)
    for row in communications:
        grouped[row["event_type"]].append(row)
    diversity = {}
    for event_type, rows in sorted(grouped.items()):
        normalized_bodies = [normalize(row["body"]) for row in rows]
        unique_bodies = len(set(normalized_bodies))
        unique_subjects = len({normalize(row["subject"]) for row in rows})
        max_similarity = 0.0
        high_pairs = 0
        pair_count = 0
        token_sets = [set(value.split()) for value in normalized_bodies]
        for left, right in combinations(range(len(rows)), 2):
            a, b = token_sets[left], token_sets[right]
            score = len(a & b) / len(a | b) if a or b else 1.0
            max_similarity = max(max_similarity, score)
            pair_count += 1
            if score >= 0.85:
                high_pairs += 1
        diversity[event_type] = {
            "records": len(rows),
            "unique_normalized_bodies": unique_bodies,
            "body_uniqueness_ratio": round(unique_bodies / len(rows), 4),
            "unique_normalized_subjects": unique_subjects,
            "subject_uniqueness_ratio": round(unique_subjects / len(rows), 4),
            "mean_body_words": round(sum(len(row["body"].split()) for row in rows) / len(rows), 2),
            "max_within_type_jaccard": round(max_similarity, 4),
            "high_similarity_pairs_ge_0_85": high_pairs,
            "within_type_pairs": pair_count,
        }

    pair_total = sum(row["within_type_pairs"] for row in diversity.values())
    high_total = sum(row["high_similarity_pairs_ge_0_85"] for row in diversity.values())
    minimum_body_ratio = min(row["body_uniqueness_ratio"] for row in diversity.values())
    # Finite deterministic template bank: report low diversity as REVIEW, not as structural failure.
    diversity_status = "PASS" if minimum_body_ratio >= 0.55 and high_total / max(pair_total, 1) <= 0.005 else "REVIEW"
    return {
        "status": "PASS" if validation["status"] == "PASS" else "FAIL",
        "structural_status": validation["status"],
        "text_diversity_status": diversity_status,
        "minimum_event_type_body_uniqueness_ratio": minimum_body_ratio,
        "high_similarity_pair_ratio": round(high_total / max(pair_total, 1), 6),
        "seed": world["seed"],
        "organizations": len(world["organizations"]),
        "deals": len(world["deals"]),
        "observable_events": len(world["observable_events"]),
        "communications": len(communications),
        "unique_source_events": validation["unique_source_events"],
        "channel_counts": channels,
        "event_type_counts": event_types,
        "missingness_preserved_records": missing,
        "speaker_turns_fabricated": sum(row["speaker_contact_id"] is not None for row in communications),
        "text_diversity_diagnostic": diversity,
        "validation_errors": validation["errors"],
        "generation_authorized": CONFIG["generation_authorized"],
        "bulk_generation_enabled": CONFIG["bulk_generation_enabled"],
        "scope": "in-memory observable-only communication rendering; no fixture writes",
        "quality_note": "Structural PASS does not mean text quality PASS. Finite template diversity remains REVIEW and requires a later paraphrase/content-generation phase; lexical metrics do not establish semantic realism or NLP suitability."
    }


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(1)
