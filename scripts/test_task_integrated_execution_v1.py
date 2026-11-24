import json
from task_integrated_execution_v1 import execute_with_tasks
from authority_execution_v1 import execute_authoritative
def main():
    inputs=dict(actor="P2",initiator="P4",requirementsMet=True,remediable=False)
    pid="technical_expertise"
    baseline=execute_authoritative(pid,inputs)
    node_events=[e for e in baseline["events"] if e["event"]=="node"]
    step=next(i for i,e in enumerate(node_events) if e["node_id"]=="technical_review")
    key="I1:technical_review:"+str(step)
    entry=dict(assigner="P1",assignee="P2",issued_at="2026-06-01T09:00:00",due_at="2026-06-02T09:00:00",completed_at="2026-06-01T10:00:00")
    plan={key:entry}
    r=execute_with_tasks(pid,inputs,plan)
    assert r["result"]==baseline["result"]
    events=[e for e in r["events"] if e["event"] in ("task_assigned","task_completed")]
    assert len(events)==2 and events[0]["assignment"]["actual_actor_id"] is None and events[1]["assignment"]["actual_actor_id"]=="P2"
    assert events[0]["instance_path"]=="I1" and events[0]["node_id"]=="technical_review"
    assert events[1]["previous_event_id"]==events[0]["event_id"]
    assert r==execute_with_tasks(pid,inputs,plan)
    negatives=0
    for bad in ({},{**plan,"unused":entry},{key:{**entry,"assigner":"P4"}},{key:{**entry,"assignee":"P3"}},{key:{**entry,"completed_at":"2026-06-03T10:00:00"}}):
        try: execute_with_tasks(pid,inputs,bad)
        except ValueError: negatives+=1
        else: raise AssertionError("invalid task plan accepted")
    print(json.dumps(dict(status="PASS",positive_cases=1,negative_cases=negatives)))
if __name__=="__main__": main()
