"""Organization-bound process audit prototype."""
import json, hashlib
import xml.etree.ElementTree as ET
from process_executor_v4 import ROOT,run,D
def load(path): return json.loads((ROOT/path).read_text())
def digest(path): return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def simulate(process_id,instance_id,initiator,actor,inputs):
    org=load("models/organization/organization_profile_v1.json")
    reg=load("models/process_registry.json")
    spec=next(p for p in reg["processes"] if p["id"]==process_id)
    people={p["id"]:p for p in org["people"]}
    roles={r["id"]:r for r in org["roles"]}
    if initiator not in people or actor not in people: raise ValueError("unknown person")
    role=roles[people[actor]["role"]]
    policy={"deal_approval":("authorized","grants","deal.approve"),"budget_approval":("authorized","grants","budget.approve"),"technical_expertise":("competent","competencies","technical.assess")}
    key,field,required=policy[process_id]
    if key in inputs: raise ValueError("authority must be derived, not supplied")
    context={**inputs,key:required in role[field]}
    result=run(spec,context)
    records=[]
    for step in result["trace"]:
        node=step["node_id"]
        record={**step,"logical_time":step["step"],"actor_id":None}
        if "decision_id" in step:
            b=spec["decisions"][node]
            record.update(actor_id=actor,actor_role="decision_subject",authority_source={"role":role["id"],"field":field,"required":required,"granted":context[key]},decision_model_sha256=digest(b["file"]))
        if node in {"approve","reject","deny","escalate","recommend_accept","recommend_rework","recommend_reject","refer_expert"}:
            record.update(actor_id=actor,actor_role="assigned_action_actor")
        records.append(record)
        context.update(spec.get("updates",{}).get(node,{}))
    return {"instance_id":instance_id,"organization_id":org["organization_id"],"process_id":process_id,"initiator_id":initiator,"bpmn_sha256":digest(spec["bpmn"]),"organization_sha256":digest("models/organization/organization_profile_v1.json"),"end":result["end"],"records":records}
if __name__=="__main__":
    cases=[
      ("deal_approval","P4","P1",dict(requirementsMet=False,revisionAllowed=True),"end"),
      ("deal_approval","P4","P2",dict(requirementsMet=True,revisionAllowed=False),"blocked"),
      ("budget_approval","P4","P3",dict(fundsAvailable=True,withinLimit=False),"escalated"),
      ("technical_expertise","P1","P2",dict(requirementsMet=False,remediable=True),"rework"),
      ("technical_expertise","P1","P4",dict(requirementsMet=True,remediable=False),"referred")]
    reports=[]
    for i,(p,initiator,actor,inputs,end) in enumerate(cases):
        args=(p,f"I{i+1}",initiator,actor,inputs)
        a=simulate(*args)
        assert a["end"]==end and a==simulate(*args)
        assert all(r["rule_id"] for r in a["records"] if "decision_id" in r)
        reports.append(a)
    try: simulate("deal_approval","bad","P4","P2",dict(authorized=True,requirementsMet=True,revisionAllowed=False))
    except ValueError: pass
    else: raise AssertionError("authority override accepted")
    print(json.dumps({"status":"PASS","instances":reports,"authority_override":"PASS"},indent=2))
