"""Nested process projection and decision replay regression."""
import json
from copy import deepcopy
from corporate_multilevel_v4 import run,readiness,READINESS,MODEL
from organization_decision_audit import digest
from test_decision_evidence_v2 import validate
def require(ok,message):
    if not ok: raise ValueError(message)
def audit(r):
    root=r["instance_id"]; children=r["children"]; events=r["events"]
    require(r["model_sha256"]==digest(MODEL),"parent model")
    require([e["global_step"] for e in events]==list(range(len(events))),"global order")
    expected={}
    for child in children.values():
        cid=child["instance_id"]
        require(cid.startswith(root+"/") and cid not in expected,"child identity")
        if "records" in child:
            validate(child); expected[cid]=child["records"]
        else:
            expected[cid]=[]
            for i,a in enumerate(child["attempts"],1):
                expected[cid].append(dict(attempt=i,actor=a["actor"],limit=a["limit"],outcome=a["outcome"]))
                if "audit" in a:
                    sub=a["audit"]; sid=cid+"/"+str(i)
                    require(sub["instance_id"]==sid and sid not in expected,"attempt identity")
                    validate(sub); expected[sid]=sub["records"]
    actual={p:[] for p in expected}
    for e in events:
        p=e["instance_path"]
        require(p==root or p in actual,"orphan event")
        if p!=root: actual[p].append(e["record"])
    require(actual==expected,"child projection mismatch")
    parent=[e["record"] for e in events if e["instance_path"]==root]
    decisions=[e for e in parent if e.get("decision_id")=="corporate_readiness"]
    require(len(decisions)==1,"readiness count")
    d=decisions[0]
    inputs=dict(technicalStatus=children["technical_expertise"]["end"],budgetStatus=children["budget_escalation"]["outcome"])
    outcome,rule=readiness(inputs)
    require(d["inputs"]==inputs and d["outcome"]==outcome and d["rule_id"]==rule and d["dmn_sha256"]==digest(READINESS),"readiness evidence")
    require(("deal_approval" in children)==(outcome!="pending"),"deal routing")
    if outcome=="pending": require(r["decision"]=="pending","pending outcome")
    else:
        leaf=children["deal_approval"]
        last=[x for x in leaf["records"] if "decision_id" in x][-1]
        require(last["inputs"]["requirementsMet"]==(outcome=="ready") and last["outcome"]==r["decision"],"deal input/output")
    return len(expected)
def main():
    cases=[]
    for amount,expected in [(500000,"approve"),(500001,"approve"),(5000001,"pending")]:
        args=("N"+str(amount),dict(requirementsMet=True,remediable=False),dict(amount=amount,funds=True,as_of="2026-06-01"),dict(initiator="P4",technical_expertise="P2",budget_approval="P3",deal_approval="P1"))
        r=run(*args); require(r==run(*args) and r["decision"]==expected,"regression")
        cases.append(dict(amount=amount,paths=audit(r)))
    r=run("mutation",dict(requirementsMet=True,remediable=False),dict(amount=500001,funds=True,as_of="2026-06-01"),dict(initiator="P4",technical_expertise="P2",budget_approval="P3",deal_approval="P1"))
    rejected=[]
    for name in ("orphan","order","missing","duplicate","outcome"):
        bad=deepcopy(r)
        e=next(e for e in bad["events"] if e["instance_path"]!="mutation")
        if name=="orphan": e["instance_path"]="unknown"
        elif name=="order": e["global_step"]=-1
        elif name=="missing": bad["events"].remove(e)
        elif name=="duplicate": bad["events"].append(deepcopy(e))
        else: bad["decision"]="deny"
        try: audit(bad)
        except ValueError: rejected.append(name)
        else: raise AssertionError(name)
    print(json.dumps(dict(status="PASS",cases=cases,mutations_rejected=rejected),indent=2))
if __name__=="__main__": main()
