"""Restricted BPMN escalation runner; reuse existing budget DMN."""
import json
from datetime import date
import xml.etree.ElementTree as ET
from organization_decision_audit import simulate,load,digest
from process_executor_v4 import ROOT,B
MODEL="models/bpmn/budget_escalation.bpmn"
GRANTS="models/organization/budget_authority_v1.json"
def escalate(instance,amount,funds,as_of,start="P3"):
    if type(amount) is not int or amount<=0 or type(funds) is not bool: raise ValueError("invalid inputs")
    day=date.fromisoformat(as_of)
    org=load("models/organization/organization_profile_v1.json")
    people={p["id"]:p for p in org["people"]}
    grants=load(GRANTS)["grants"]
    p=ET.parse(ROOT/MODEL).getroot().find(B+"process")
    nodes={n.get("id"):n for n in p if n.tag!=B+"sequenceFlow"}
    flows=p.findall(B+"sequenceFlow")
    actor=start; current="start"; seen=set(); attempts=[]; trace=[]; cont=False; outcome=None
    for step in range(100):
        n=nodes[current]; trace.append(current)
        if n.tag==B+"endEvent":
            return dict(instance_id=instance,amount=amount,currency="RUB",as_of=as_of,outcome=outcome,attempts=attempts,trace=trace,model_sha256=digest(MODEL),grants_sha256=digest(GRANTS))
        if n.tag==B+"callActivity":
            if actor not in people or actor in seen: raise ValueError("invalid hierarchy")
            seen.add(actor)
            active=[g for g in grants if g["person"]==actor and date.fromisoformat(g["valid_from"])<=day<=date.fromisoformat(g["valid_to"])]
            if len(active)>1: raise ValueError("ambiguous grant")
            limit=active[0]["limit"] if active else None
            if limit is None:
                outcome="no_active_grant"; cont=False
                attempts.append(dict(actor=actor,limit=None,outcome=outcome))
            else:
                audit=simulate("budget_approval",instance+"/"+str(len(attempts)+1),"P4",actor,dict(fundsAvailable=funds,withinLimit=amount<=limit))
                outcome=audit["end"]
                cont=outcome=="escalated" and people[actor]["manager"] is not None
                if outcome=="escalated" and not cont: outcome="unresolved_limit"
                attempts.append(dict(actor=actor,limit=limit,outcome=outcome,audit=audit))
        elif current=="advance_manager": actor=people[actor]["manager"]
        outgoing=[]
        for f in flows:
            if f.get("sourceRef")!=current: continue
            c=f.find(B+"conditionExpression")
            if c is None or c.text==("continue = true" if cont else "continue = false"): outgoing.append(f)
        if len(outgoing)!=1: raise ValueError("invalid transition")
        current=outgoing[0].get("targetRef")
    raise RuntimeError("step limit")
if __name__=="__main__":
    cases=[]
    for amount,funds,day,expected,count in [(500000,True,"2026-06-01","approved",1),(500001,True,"2026-06-01","approved",2),(5000000,True,"2026-06-01","approved",2),(5000001,True,"2026-06-01","unresolved_limit",2),(100,False,"2026-06-01","rejected",1),(100,True,"2027-01-01","no_active_grant",1)]:
        args=("B"+str(len(cases)+1),amount,funds,day)
        r=escalate(*args)
        assert r["outcome"]==expected and len(r["attempts"])==count and r==escalate(*args)
        cases.append(r)
    print(json.dumps({"status":"PASS","cases":cases},indent=2))
