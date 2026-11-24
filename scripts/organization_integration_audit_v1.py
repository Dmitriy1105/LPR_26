"""Cross-module integration audit. Explicitly distinguishes supported links from full event equivalence."""
from organization_engine_v1 import generate
from roles_competencies_v1 import build,validate as validate_roles
from temporal_authority_v1 import validate_grants,authorize_at
from financial_authority_v1 import validate_bands,evaluate_financial_authority
from delegation_authority_v1 import validate_delegations,authorize_delegated_at
from organizational_changes_v1 import validate_events as validate_org_events,project_at
from event_chronology_v1 import validate_events as validate_chronology,chronology
from organization_process_integration_v1 import evaluate_task,build_decision_trace
def audit():
    org=generate(seed=42,count=1)[0]; people=org["people"]; actor=people[0]["id"]; delegate=people[1]["id"]
    roles=build(org); validate_roles(org,roles)
    grants=[dict(grant_id="G-D",org_id=org["id"],person_id=actor,action="contract",permission="delegate",valid_from="2026-01-01",valid_until="2027-01-01",max_amount=50000,source_ref="authority-resolution"),dict(grant_id="G-A",org_id=org["id"],person_id=actor,action="contract",permission="final_decision",valid_from="2026-01-01",valid_until="2027-01-01",max_amount=50000,source_ref="authority-resolution")]
    bands=[dict(band_id="B1",org_id=org["id"],person_id=actor,action="contract",permission="approve",currency="SGD",min_amount=0,max_amount=10000,valid_from="2026-01-01",valid_until="2027-01-01",source_ref="finance-policy")]
    delegations=[dict(delegation_id="D1",org_id=org["id"],delegator_id=actor,delegatee_id=delegate,source_grant_id="G-D",action="contract",permission="approve",valid_from="2026-02-01",valid_until="2026-12-01",max_amount=20000,source_ref="delegation-order",redelegation=False)]
    org_events=[dict(event_id="O1",org_id=org["id"],person_id=delegate,kind="transfer",effective_date="2026-03-01",new_unit=org["units"][2]["id"],source_ref="hr-order")]
    events=[dict(event_id="E1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:02:00+08:00",actor_id=actor,subject_id="CONTRACT-1",source_ref="minutes"),dict(event_id="E2",event_type="approval",occurred_at="2026-06-01T09:03:00+08:00",recorded_at="2026-06-01T09:04:00+08:00",actor_id=delegate,subject_id="CONTRACT-1",source_ref="approval",causation_id="E1",correlation_id="C1")]
    checks={}
    checks["role_to_person_coverage"]=len(roles)==len(people)
    checks["temporal_authority"]=validate_grants(org,grants) and authorize_at(org,grants,actor,"contract","final_decision","2026-06-01",10000)["authorized"]
    checks["financial_authority"]=validate_bands(org,bands) and evaluate_financial_authority(org,bands,actor,"contract","approve",5000,"SGD","2026-06-01")["authorized"]
    checks["delegation_chain"]=validate_delegations(org,grants,delegations) and authorize_delegated_at(org,grants,delegations,delegate,"contract","approve","2026-06-01",10000)["authorized"]
    checks["organizational_history"]=validate_org_events(org,org_events) and project_at(org,org_events,"2026-04-01")[delegate]["unit"]==org["units"][2]["id"]
    checks["event_causation"]=validate_chronology(events) and [e["event_id"] for e in chronology(events)]==["E1","E2"]
    task=dict(task_id="T1",action="contract",required_permission="approve",actor_id=delegate,subject_id="CONTRACT-1",bpmn_process_id="BP1",bpmn_task_id="Approve",dmn_decision_id="DMN1")
    result=evaluate_task(org,task,grants,delegations,events,"2026-06-01",10000)
    checks["bpmn_authority_event_link"]=result["decision"]=="ALLOW" and result["authority_source"]=="delegated" and result["event_evidence_count"]==1
    trace=build_decision_trace(result,dict(decision_id="DMN1",outcome="APPROVE"),["E1","E2"])
    checks["decision_trace"]=trace["integrity_status"]=="evidence_linked" and trace["event_ids"]==["E1","E2"]
    return dict(schema_version="1.0",status="PASS" if all(checks.values()) else "FAIL",checks=checks,passed=sum(checks.values()),total=len(checks),limitations=["This audit checks module-level joins and a synthetic happy path; it does not prove complete equivalence between independent event journals.","The process adapter records a DMN reference and outcome but does not execute a full DMN decision table.","The organizational history projection is not yet automatically reconciled with authority-grant history."])
def main():
    import json
    r=audit(); print(json.dumps(r,ensure_ascii=False,sort_keys=True))
    if r["status"]!="PASS": raise SystemExit(1)
if __name__=="__main__": main()
