"""GEN-010.7 canonical-ID BPMN/DMN leaf execution and event reconciliation.

Executes the registered deal_approval BPMN/DMN leaf process for all 800 canonical
deals. Composite callActivity orchestration is not claimed: the current restricted
executor does not implement BPMN callActivity semantics.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from generator_v4_scenario_engine_v1 import build as build_scenario
from generator_v4_authority_adapter_v1 import to_legacy_org
from temporal_authority_v1 import authorize_at
from process_executor_v4 import run as run_bpmn_dmn

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "models" / "process_registry.json").read_text(encoding="utf-8"))
CONFIG = json.loads((ROOT / "config" / "generator_v4_0.json").read_text(encoding="utf-8"))
PROCESS = next(p for p in REGISTRY["processes"] if p["id"] == "deal_approval")

def _authority_rows(org, grants):
    rows = []
    for grant in grants:
        if grant["organization_id"] != org["organization_id"]:
            continue
        rows.append({
            "grant_id": grant["grant_id"], "org_id": org["organization_id"],
            "person_id": grant["contact_id"], "action": "approve_deal",
            "permission": "final_decision", "valid_from": grant["valid_from"][:10],
            "valid_until": None, "revoked_at": None, "status": "active",
            "source_ref": grant["source_ref"]
        })
    return rows

def audit():
    world = build_scenario(config=CONFIG)
    orgs = {o["organization_id"]: o for o in world["organizations"]}
    grants = {oid: _authority_rows(org, world["authority_grants"]) for oid, org in orgs.items()}
    event_groups = {}
    for event in world["events"]:
        event_groups.setdefault(event["deal_id"], []).append(event)
    truth = {row["deal_id"]: row for row in world["ground_truth"]["records"]
             if row["event_type"] in ("approve", "reject")}
    results, errors = [], []
    outcomes = Counter()
    for deal in world["deals"]:
        rows = sorted(event_groups[deal["deal_id"]], key=lambda x: x["occurred_at"])
        final = [e for e in rows if e["event_type"] in ("approve", "reject")]
        if len(final) != 1:
            errors.append({"deal_id": deal["deal_id"], "error": "not_exactly_one_final_decision"})
            continue
        decision = final[0]
        org = orgs[decision["organization_id"]]
        auth = authorize_at(to_legacy_org(org), grants[decision["organization_id"]],
            decision["actor_contact_id"], "approve_deal", "final_decision",
            decision["occurred_at"][:10])
        if not auth.get("authorized") or auth.get("grant_id") != decision["authority_grant_ref"]:
            errors.append({"deal_id": deal["deal_id"], "error": "authority_mismatch", "authority": auth})
            continue
        expected = "reject" if deal["family"] == "rejected" else "approve"
        execution = run_bpmn_dmn(PROCESS, {
            "authorized": True, "requirementsMet": deal["family"] != "rejected",
            "revisionAllowed": False
        })
        actual = execution["context"].get("outcome")
        if actual != expected:
            errors.append({"deal_id": deal["deal_id"], "error": "process_outcome_mismatch",
                           "expected": expected, "actual": actual})
        terminal = "end"
        if execution["end"] != terminal:
            errors.append({"deal_id": deal["deal_id"], "error": "unexpected_process_terminal",
                           "terminal": execution["end"]})
        gold = truth.get(deal["deal_id"])
        if not gold or gold["actor_contact_id"] != decision["actor_contact_id"]:
            errors.append({"deal_id": deal["deal_id"], "error": "ground_truth_decision_actor_mismatch"})
        close = rows[-1]
        if close["event_type"] != "close" or close["decision_outcome"] != deal["status"]:
            errors.append({"deal_id": deal["deal_id"], "error": "event_journal_close_mismatch"})
        outcomes[actual] += 1
        results.append({
            "deal_id": deal["deal_id"], "organization_id": deal["organization_id"],
            "scenario_family": deal["family"], "event_decision_id": decision["event_id"],
            "decision_actor_contact_id": decision["actor_contact_id"],
            "authority_grant_ref": auth.get("grant_id"), "bpmn_process_id": PROCESS["id"],
            "dmn_decision_id": PROCESS["decisions"]["decide"]["id"],
            "bpmn_terminal": execution["end"], "dmn_outcome": actual,
            "expected_outcome": expected, "outcome_match": actual == expected,
            "event_close_id": close["event_id"],
            "event_close_matches": close["decision_outcome"] == deal["status"],
            "trace": execution["trace"]
        })
    return {
        "status": "PASS" if not errors and len(results) == 800 else "FAIL",
        "seed": world["seed"], "organizations": len(world["organizations"]),
        "deals": len(world["deals"]), "bpmn_dmn_executions": len(results),
        "matched_outcomes": sum(r["outcome_match"] for r in results),
        "event_close_matches": sum(r["event_close_matches"] for r in results),
        "authority_checks": len(results), "outcome_distribution": dict(outcomes),
        "errors": errors, "results": results,
        "scope": "registered deal_approval BPMN/DMN leaf process only",
        "composite_call_activity_execution": "NOT_IMPLEMENTED_BY_RESTRICTED_EXECUTOR",
        "generation_authorized": CONFIG["generation_authorized"],
        "bulk_generation_enabled": CONFIG["bulk_generation_enabled"]
    }

if __name__ == "__main__":
    report = audit()
    print(json.dumps({k:v for k,v in report.items() if k != "results"},
                     ensure_ascii=False, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(1)
