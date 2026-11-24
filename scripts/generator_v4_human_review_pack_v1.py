"""GEN-010.11A deterministic blinded human-review pack builder.

Creates a text-only reviewer pack and a separate evaluator answer key. No CRM fixture
or persistent corpus is written. The key must not be shared with blinded reviewers.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from generator_v4_scenario_engine_v1 import build
from generator_v4_communication_renderer_v1 import render_communications
from generator_v4_composite_bpmn_audit_v1 import CONFIG

EVENT_TYPES = (
    "request_information", "delegate", "complete_task", "review", "recommend",
    "object", "revise", "unit_approval", "approve", "reject", "close"
)
SAMPLE_PER_CLASS = 20
PACK_VERSION = "1.0.0"


def _stable_rank(seed: int, event_type: str, source_id: str) -> str:
    return hashlib.sha256(f"{seed}|GEN-010.11A|{event_type}|{source_id}".encode()).hexdigest()


def _redact_deal_id(text: str) -> str:
    return re.sub(r"\bORG-\d+-D\d+\b", "[DEAL]", text or "")


def build_review_pack(communications: list[dict], seed: int = 42):
    grouped = defaultdict(list)
    for row in communications:
        grouped[row["event_type"]].append(row)
    missing = set(EVENT_TYPES) - set(grouped)
    if missing:
        raise ValueError("missing event classes: " + ", ".join(sorted(missing)))

    selected = []
    selection_audit = {}
    for event_type in EVENT_TYPES:
        candidates = sorted(
            grouped[event_type],
            key=lambda row: _stable_rank(seed, event_type, row["source_event_id"])
        )
        org_counts = Counter()
        chosen = []
        # Greedy deterministic balancing distributes the class sample over organizations.
        for row in candidates:
            oid = row["organization_id"]
            if org_counts[oid] >= 1:
                continue
            chosen.append(row)
            org_counts[oid] += 1
            if len(chosen) == SAMPLE_PER_CLASS:
                break
        if len(chosen) < SAMPLE_PER_CLASS:
            # If fewer than 20 organizations are represented, fill remaining slots
            # by stable rank while keeping selection deterministic.
            chosen_ids = {row["source_event_id"] for row in chosen}
            for row in candidates:
                if row["source_event_id"] in chosen_ids:
                    continue
                chosen.append(row)
                if len(chosen) == SAMPLE_PER_CLASS:
                    break
        if len(chosen) != SAMPLE_PER_CLASS:
            raise ValueError(f"insufficient records for {event_type}: {len(chosen)}")
        selected.extend(chosen)
        selection_audit[event_type] = {
            "population": len(candidates),
            "sample": len(chosen),
            "organizations_covered": len({row["organization_id"] for row in chosen}),
            "channels": dict(sorted(Counter(row["channel"] for row in chosen).items())),
        }

    # Interleave event classes so adjacent rows do not reveal class blocks.
    selected.sort(key=lambda row: _stable_rank(seed, "interleave", row["source_event_id"]))
    blinded_rows, key_rows = [], []
    for index, row in enumerate(selected, 1):
        review_id = f"HR-{index:03d}"
        blinded_rows.append({
            "review_id": review_id,
            "channel": row["channel"],
            "record_format": row["record_format"],
            "subject": _redact_deal_id(row["subject"]),
            "body": _redact_deal_id(row["body"]),
            "reviewer_1": {
                "primary_event_type": None,
                "secondary_signals": [],
                "event_clarity_1_to_5": None,
                "naturalness_1_to_5": None,
                "factual_support_1_to_5": None,
                "unsupported_claims": [],
                "ambiguity_notes": "",
                "reviewer_comments": ""
            },
            "reviewer_2": {
                "primary_event_type": None,
                "secondary_signals": [],
                "event_clarity_1_to_5": None,
                "naturalness_1_to_5": None,
                "factual_support_1_to_5": None,
                "unsupported_claims": [],
                "ambiguity_notes": "",
                "reviewer_comments": ""
            },
            "adjudication": {
                "primary_event_type": None,
                "reason": ""
            }
        })
        key_rows.append({
            "review_id": review_id,
            "source_event_id": row["source_event_id"],
            "source_ref": row["source_ref"],
            "organization_id": row["organization_id"],
            "deal_id": row["deal_id"],
            "ground_truth_event_type": row["event_type"],
            "channel": row["channel"],
            "occurred_at": row["occurred_at"]
        })

    pack = {
        "schema_version": PACK_VERSION,
        "audit": "GEN-010.11A",
        "title": "Blinded synthetic CRM communication review",
        "instructions": {
            "blindness": "Do not consult the separate answer key or CRM metadata while annotating.",
            "allowed_primary_event_types": list(EVENT_TYPES),
            "primary_event_type": "Choose the single best-supported event class; use unclear if no class is adequately supported.",
            "secondary_signals": "Optional additional signals; do not replace the primary class.",
            "rating_scale": "1=very poor/unclear, 5=clear/strong",
            "factual_support": "Judge only claims visible in the text; do not assume hidden scenario facts.",
            "unsupported_claims": "Quote or summarize unsupported factual assertions, roles, decisions, deadlines or outcomes.",
            "independence": "Reviewers annotate independently before discussion or adjudication."
        },
        "sample_size": len(blinded_rows),
        "per_event_class_target": SAMPLE_PER_CLASS,
        "seed": seed,
        "records": blinded_rows
    }
    answer_key = {
        "schema_version": PACK_VERSION,
        "audit": "GEN-010.11A-ANSWER-KEY",
        "restricted": True,
        "do_not_share_with_reviewers": True,
        "sample_size": len(key_rows),
        "records": key_rows
    }
    audit = {
        "status": "PASS" if len(blinded_rows) == 220 and len(key_rows) == 220 else "FAIL",
        "sample_size": len(blinded_rows),
        "unique_review_ids": len({r["review_id"] for r in blinded_rows}),
        "per_event_class": selection_audit,
        "blinded_fields": ["event_type", "source_event_id", "source_ref", "organization_id", "deal_id", "occurred_at", "contact_ids"],
        "answer_key_separate": True,
        "body_deal_ids_redacted": all("[DEAL]" in r["body"] or "ORG-" not in r["body"] for r in blinded_rows),
        "human_annotations_completed": False
    }
    return pack, answer_key, audit


def main():
    world = build(config=CONFIG)
    communications = render_communications(
        world["observable_events"], world["organizations"], world["seed"]
    )
    pack, key, audit = build_review_pack(communications, seed=world["seed"])
    print(json.dumps({"audit": audit, "review_pack": pack, "answer_key": key},
                     ensure_ascii=False, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
