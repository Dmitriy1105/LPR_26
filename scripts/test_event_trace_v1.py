import json
from copy import deepcopy
from authority_execution_v1 import execute_authoritative
def validate(r):
    events=r["events"]
    assert r["trace_version"]=="1.0" and len(r["registry_sha256"])==64
    assert len(events)>0
    local={}; active=[]; seen=set(); pending={}; previous=None
    for i,e in enumerate(events):
        p=e["instance_path"]; t=e["event"]; eid=e["event_id"]
        assert e["global_step"]==i and eid not in seen
        assert e["previous_event_id"]==previous and e["previous_local_event_id"]==local.get(p)
        if t=="process_start":
            assert p not in local and len(e["bpmn_sha256"])==64
            assert e["parent_instance_path"]==(active[-1] if active else None)
            if active: assert pending[active[-1]]==p
            active.append(p)
        assert active and active[-1]==p
        if t=="call_start":
            assert p not in pending
            pending[p]=e["child_id"]
        if t=="call_end":
            assert pending.pop(p)==e["child_id"] and e["child_id"] in local
        if t=="decision":
            assert len(e["dmn_sha256"])==64 and e["rule_id"] and "inputs" in e and "actor_id" in e
        if t=="process_end":
            assert p not in pending
            active.pop()
        seen.add(eid); local[p]=eid; previous=eid
    assert not active and not pending
    assert events[-1]["event"]=="process_end"
def main():
    cases=[]
    for amount in (500000,500001,5000001):
        inputs=dict(technicalActor="P2",budgetActor="P3",dealActor="P1",initiator="P4",amount=amount,as_of="2026-06-01",fundsAvailable=True,technicalRequirementsMet=True,remediable=False)
        r=execute_authoritative("corporate_multilevel_universal",inputs)
        validate(r)
        assert r==execute_authoritative("corporate_multilevel_universal",inputs)
        cases.append(dict(amount=amount,events=len(r["events"])))
    negatives=0
    for key,value in [("event_id",r["events"][0]["event_id"]),("previous_event_id","bad"),("previous_local_event_id","bad"),("global_step",-1),("instance_path","orphan")]:
        bad=deepcopy(r); bad["events"][1][key]=value
        try: validate(bad)
        except (AssertionError,KeyError): negatives+=1
        else: raise AssertionError("mutation accepted")
    print(json.dumps(dict(status="PASS",cases=cases,negative_tests=negatives)))
if __name__=="__main__": main()
