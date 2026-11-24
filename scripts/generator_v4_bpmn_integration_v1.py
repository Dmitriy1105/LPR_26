"""Bridge synthetic Scenario Engine deals into authoritative BPMN/DMN execution."""
import json
import subprocess
from pathlib import Path
from authority_execution_v1 import execute_authoritative

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
ORGANIZATIONS = 5
DEALS_PER_ORGANIZATION = 6

def generate_world(seed=SEED):
    code = (
        "import { generate } from './scripts/scenario_engine_v4.mjs'; "
        f"process.stdout.write(JSON.stringify(generate({{seed:{seed},organizations:{ORGANIZATIONS},dealsPerOrganization:{DEALS_PER_ORGANIZATION}}})));"
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", code],
        cwd=ROOT, check=True, capture_output=True, text=True
    )
    return json.loads(completed.stdout)

def execute_scenarios(world):
    # These IDs are the approved demo organization's role fixtures:
    # P1 director, P2 technical expert, P3 finance manager, P4 buyer/initiator.
    # The mapping is explicit and is not inferred from generated names.
    actor_map = {
        "technicalActor": "P2",
        "budgetActor": "P3",
        "dealActor": "P1",
        "initiator": "P4",
    }
    results = []
    for deal in world["deals"]:
        family = deal["family"]
        expected = "reject" if family == "rejected" else "approve"
        inputs = {
            **actor_map,
            "amount": 10000,
            "as_of": "2026-06-01",
            "fundsAvailable": True,
            "technicalRequirementsMet": family != "rejected",
            "remediable": False,
        }
        execution = execute_authoritative(
            "corporate_multilevel_universal",
            inputs,
            instance="GEN2:" + deal["id"],
        )
        context = execution["result"]["context"]
        actual = context.get("dealOutcome")
        if execution["result"]["end"] == "pending":
            actual = "pending"
        results.append({
            "deal_id": deal["id"],
            "family": family,
            "expected": expected,
            "actual": actual,
            "match": actual == expected,
            "process_id": "corporate_multilevel_universal",
            "end": execution["result"]["end"],
            "event_count": len(execution["events"]),
            "decision_events": [
                {"decision_id": e.get("decision_id"), "outcome": e.get("outcome"), "actor_id": e.get("actor_id")}
                for e in execution["events"] if e.get("event") == "decision"
            ],
        })
    return results

def audit(seed=SEED):
    world = generate_world(seed)
    scenario_validation = __import__("subprocess").run(
        ["node", "--input-type=module", "-e",
         "import {generate,validate} from './scripts/scenario_engine_v4.mjs'; "
         f"const w=generate({{seed:{seed},organizations:{ORGANIZATIONS},dealsPerOrganization:{DEALS_PER_ORGANIZATION}}}); "
         "const r=validate(w); process.stdout.write(JSON.stringify(r)); if(!r.pass) process.exit(2);"],
        cwd=ROOT, check=True, capture_output=True, text=True
    )
    validation = json.loads(scenario_validation.stdout)
    results = execute_scenarios(world)
    mismatches = [r for r in results if not r["match"]]
    return {
        "status": "PASS" if validation["pass"] and not mismatches else "FAIL",
        "seed": seed,
        "organization_count": len(world["organizations"]),
        "deal_count": len(world["deals"]),
        "scenario_validation": validation,
        "process_execution_count": len(results),
        "matched_outcomes": len(results) - len(mismatches),
        "mismatches": mismatches,
        "results": results,
    }

def main():
    first = audit(42)
    second = audit(42)
    assert first == second, "same seed must reproduce identical scenario-to-process results"
    assert first["status"] == "PASS", json.dumps(first, ensure_ascii=False)
    assert first["organization_count"] == 5
    assert first["deal_count"] == 30
    assert first["process_execution_count"] == 30
    assert first["matched_outcomes"] == 30
    print(json.dumps({
        "status": first["status"],
        "seed": first["seed"],
        "organizations": first["organization_count"],
        "deals": first["deal_count"],
        "bpmn_dmn_executions": first["process_execution_count"],
        "matched_outcomes": first["matched_outcomes"],
        "deterministic": True,
    }, ensure_ascii=False, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
