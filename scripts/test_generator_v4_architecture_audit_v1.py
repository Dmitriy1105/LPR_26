import json
from generator_v4_architecture_audit_v1 import audit

def main():
    report=audit()
    findings={x["id"]:x for x in report["findings"]}
    assert report["status"]=="REVIEW_REQUIRED"
    assert len(findings)==9
    assert report["contract_status"].startswith("APPROVED PROJECT REQUIREMENTS")
    assert findings["GEN-001"]["status"] in ("OPEN","CLOSED")
    assert report["checks"]["scenario_negative_test_pass"] == (findings["GEN-001"]["status"]=="CLOSED")
    assert report["scenario_smoke"]["negative_test"]["pass"] is False
    assert report["fixture_total"]==677
    assert report["contract_baseline_target"]==767
    assert findings["GEN-002"]["status"]=="CLOSED"
    assert report["checks"]["e2e_executes_scenario_or_bpmn_runtime"] is True
    assert report["bpmn_dmn_integration"]["bpmn_dmn_executions"]==30
    assert report["bpmn_dmn_integration"]["matched_outcomes"]==30
    assert findings["GEN-003"]["status"]=="CLOSED"
    assert report["checks"]["scenario_engine_emits_crm_communications"] is True
    assert report["communication_generation"]["communications"]==report["communication_generation"]["source_events"]
    assert report["communication_generation"]["deterministic"] is True
    assert findings["GEN-004"]["status"]=="OPEN"
    assert findings["GEN-006"]["status"]=="CLOSED"
    assert len(report["prior_architecture_partial_ids"])>=1
    assert findings["GEN-008"]["status"]=="DECISION_REQUIRED"
    assert findings["GEN-009"]["status"]=="DECISION_REQUIRED"
    assert all(x["evidence"] for x in report["findings"])
    print(json.dumps({"status":"PASS","audit_status":report["status"],"findings":len(findings),"open_findings":sum(x["status"]=="OPEN" for x in findings.values()),"decision_required":sum(x["status"]=="DECISION_REQUIRED" for x in findings.values()),"fixture_total":report["fixture_total"],"contract_target":report["contract_baseline_target"],"contract_approved":report["checks"]["data_contract_approved"]}))
if __name__=="__main__":
    main()
