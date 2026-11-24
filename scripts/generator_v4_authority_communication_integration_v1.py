"""GEN-010.6 bounded integration: canonical events through temporal authority engine.

The legacy BPMN executor and legacy communication renderer are deliberately not
invoked here: both still consume the six-person demo world. This adapter proves
canonical identity + time-valid authority integration without silently remapping IDs.
"""
from __future__ import annotations

import json
from pathlib import Path

from generator_v4_scenario_engine_v1 import build as build_scenario
from generator_v4_authority_adapter_v1 import to_legacy_org
from temporal_authority_v1 import authorize_at, validate_grants

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "generator_v4_0.json").read_text(encoding="utf-8"))


def _temporal_grants(org, canonical_grants):
    rows = []
    for grant in canonical_grants:
        if grant["organization_id"] != org["organization_id"]:
            continue
        scope = grant["scope"]
        if scope == "deal_approval":
            action, permission = "approve_deal", "final_decision"
        elif scope.startswith("unit_approval:"):
            action, permission = "approve_unit", "approve"
        else:
            raise ValueError("unsupported canonical authority scope: " + scope)
        rows.append({
            "grant_id": grant["grant_id"],
            "org_id": org["organization_id"],
            "person_id": grant["contact_id"],
            "action": action,
            "permission": permission,
            "valid_from": grant["valid_from"][:10],
            "valid_until": None,
            "revoked_at": None,
            "status": "active",
            "source_ref": grant["source_ref"]
        })
    return rows


def audit():
    dataset = build_scenario(config=CONFIG)
    orgs = {o["organization_id"]: o for o in dataset["organizations"]}
    grants_by_org = {oid: _temporal_grants(org, dataset["authority_grants"])
                     for oid, org in orgs.items()}
    for oid, org in orgs.items():
        validate_grants(to_legacy_org(org), grants_by_org[oid])

    decisions = [e for e in dataset["events"]
                 if e["event_type"] in ("approve", "reject", "unit_approval")]
    checked = []
    errors = []
    for event in decisions:
        org = orgs[event["organization_id"]]
        if event["event_type"] == "unit_approval":
            action, permission = "approve_unit", "approve"
        else:
            action, permission = "approve_deal", "final_decision"
        result = authorize_at(
            to_legacy_org(org), grants_by_org[event["organization_id"]],
            event["actor_contact_id"], action, permission,
            event["occurred_at"][:10]
        )
        expected_ref = event["authority_grant_ref"]
        ok = result.get("authorized") is True and result.get("grant_id") == expected_ref
        if not ok:
            errors.append({"event_id": event["event_id"], "result": result,
                           "expected_grant_ref": expected_ref})
        checked.append({"event_id": event["event_id"], "authorized": result.get("authorized"),
                        "grant_id": result.get("grant_id"), "expected_grant_ref": expected_ref})

    # Communication projection: one observable record per event, no fabricated
    # prose, preserving stable source and participant/actor/target references.
    communications = []
    for event in dataset["observable_events"]:
        communications.append({
            "source_ref": event["source_ref"],
            "event_id": event["event_id"],
            "deal_id": event["deal_id"],
            "organization_id": event["organization_id"],
            "author_contact_id": event["actor_contact_id"],
            "participant_contact_ids": [event["actor_contact_id"]] +
                ([event["target_contact_id"]] if event["target_contact_id"] else []),
            "addressee_contact_ids": [event["target_contact_id"]] if event["target_contact_id"] else [],
            "channel": {
                "request_information": "email", "delegate": "email",
                "complete_task": "call", "review": "meeting",
                "recommend": "email", "object": "email", "revise": "call",
                "unit_approval": "meeting", "approve": "meeting",
                "reject": "meeting", "close": "meeting"
            }[event["event_type"]],
            "text_rendering_status": "not_rendered",
            "missing_fields": event["missing_fields"]
        })

    expected_authority_checks = 1040
    return {
        "status": "PASS" if not errors and len(checked) == expected_authority_checks else "FAIL",
        "seed": dataset["seed"],
        "organizations": len(orgs),
        "deals": len(dataset["deals"]),
        "events": len(dataset["events"]),
        "authority_decisions_checked": len(checked),
        "authority_checks_expected": expected_authority_checks,
        "authority_errors": errors,
        "communication_projection_records": len(communications),
        "communication_event_coverage": len(communications) == len(dataset["events"]),
        "communication_texts_rendered": 0,
        "bpmn_execution": "BLOCKED_LEGACY_RUNTIME_USES_DEMO_ACTORS",
        "generation_authorized": CONFIG["generation_authorized"],
        "bulk_generation_enabled": CONFIG["bulk_generation_enabled"],
        "scope": "in-memory canonical authority integration and metadata-only communication projection"
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
