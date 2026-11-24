import json
from generator_v4_architecture_audit_v1 import audit

def main():
    report=audit()
    findings={x["id"]:x for x in report["findings"]}
    assert report["status"]=="REVIEW_REQUIRED"
    assert len(findings)==9
    assert report["contract_status"]=="PROPOSAL_REVIEW_REQUIRED"
    assert findings["GEN-001"]["status"]=="OPEN"
    assert report["scenario_smoke"]["negative_test"]["pass"] is False
    assert report["fixture_total"]==677
    assert report["contract_baseline_target"]==767
    assert findings["GEN-002"]["status"]=="OPEN"
    assert findings["GEN-003"]["status"]=="OPEN"
    assert findings["GEN-004"]["status"]=="OPEN"
    assert findings["GEN-006"]["status"]=="OPEN"
    assert len(report["prior_architecture_partial_ids"])>=1
    assert findings["GEN-008"]["status"]=="DECISION_REQUIRED"
    assert findings["GEN-009"]["status"]=="DECISION_REQUIRED"
    assert all(x["evidence"] for x in report["findings"])
    print(json.dumps({"status":"PASS","audit_status":report["status"],"findings":len(findings),"open_findings":sum(x["status"]=="OPEN" for x in findings.values()),"decision_required":sum(x["status"]=="DECISION_REQUIRED" for x in findings.values()),"fixture_total":report["fixture_total"],"contract_target":report["contract_baseline_target"]}))
if __name__=="__main__":
    main()
