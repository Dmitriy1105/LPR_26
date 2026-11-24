import json
from copy import deepcopy
from authority_execution_v1 import execute_authoritative
from task_integrated_execution_v1 import execute_with_tasks
from actor_trace_v1 import project,replay
def main():
    pid="corporate_multilevel_universal"
    inputs=dict(technicalActor="P2",budgetActor="P3",dealActor="P1",initiator="P4",amount=500001,as_of="2026-06-01",fundsAvailable=True,technicalRequirementsMet=True,remediable=False)
    baseline=execute_authoritative(pid,inputs)
    counts={}; plan={}
    for e in baseline["events"]:
        path=e["instance_path"]
        if e["event"]!="node": continue
        step=counts.get(path,0); counts[path]=step+1
        node=e["node_id"]
        if node in ("technical_review","financial_review","complete"):
            plan[path+":"+node+":"+str(step)]=dict(assigner="P1",assignee="P3" if node=="financial_review" else "P2",issued_at="2026-06-01T09:00:00",due_at="2026-06-02T09:00:00",completed_at="2026-06-01T10:00:00")
    r=execute_with_tasks(pid,inputs,plan); rows=project(r)
    assert len(plan)>=3 and len([x for x in rows if x["event"]=="task_completed"])==len(plan)
    assert all(x["decision_actor_id"] is None for x in rows)
    assert replay(r,pid,inputs,plan)["status"]=="PASS"
    negatives=0
    for field,value in (("actual_actor_id","P4"),("delegator_id","P4"),("instance_id","wrong"),("completed_at","2026-06-03T00:00:00"),("decision_authority_transferred",True)):
        bad=deepcopy(r); e=next(x for x in bad["events"] if x["event"]=="task_completed"); e["assignment"][field]=value
        for fn in (lambda:project(bad),lambda:replay(bad,pid,inputs,plan)):
            try: fn()
            except ValueError: negatives+=1
            else: raise AssertionError("mutation accepted")
    print(json.dumps(dict(status="PASS",positive_cases=1,negative_cases=negatives,assignments=len(plan),rows=len(rows))))
if __name__=="__main__": main()
