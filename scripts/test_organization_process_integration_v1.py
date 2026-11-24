import json
from copy import deepcopy
from organization_engine_v1 import generate
from organization_process_integration_v1 import evaluate_task,build_decision_trace
def main():
    org=generate(count=1)[0]; a,b=org["people"][0]["id"],org["people"][1]["id"]
    grants=[dict(grant_id="G1",org_id=org["id"],person_id=a,action="contract",permission="final_decision",valid_from="2026-01-01",valid_until="2027-01-01",source_ref="board-resolution")]
    delegations=[]
    events=[dict(event_id="E1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=a,subject_id="DEAL-1",source_ref="meeting-minutes")]
    task=dict(task_id="T1",action="contract",required_permission="final_decision",actor_id=a,subject_id="DEAL-1",bpmn_process_id="P1",bpmn_task_id="ApproveContract",dmn_decision_id="D1")
    result=evaluate_task(org,task,grants,delegations,events,"2026-06-01")
    assert result["authorized"] and result["decision"]=="ALLOW" and result["event_evidence_count"]==1
    trace=build_decision_trace(result,dict(decision_id="D1",outcome="APPROVE"),["E1"])
    assert trace["integrity_status"]=="evidence_linked"
    denied=evaluate_task(org,dict(task,actor_id=b),grants,delegations,events,"2026-06-01")
    assert denied["decision"]=="DENY"
    negatives=0
    for mutate in (lambda x:x.pop("bpmn_task_id"),lambda x:x.update(required_permission="influence"),lambda x:x.update(actor_id="unknown")):
        bad=deepcopy(task); mutate(bad)
        try: evaluate_task(org,bad,grants,delegations,events,"2026-06-01")
        except (ValueError,KeyError): negatives+=1
        else: raise AssertionError("invalid process binding accepted")
    try: build_decision_trace(result,dict(outcome="APPROVE"),["E1"])
    except ValueError: negatives+=1
    else: raise AssertionError("invalid DMN decision accepted")
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=4)))
if __name__=="__main__": main()
