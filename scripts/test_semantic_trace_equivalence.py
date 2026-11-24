"""Compare independently projected business decisions; explicit legacy gaps."""
import json
from itertools import product
from copy import deepcopy
from corporate_multilevel_v4 import run as legacy
from authority_execution_v1 import execute_authoritative
def old_projection(r):
    out=[]
    for e in r["events"]:
        x=e["record"]
        if "attempt" in x:
            out.append(("budget_attempt",x["actor"],x["limit"],{"unresolved_limit":"escalated","no_active_grant":"blocked"}.get(x["outcome"],x["outcome"])))
        elif "decision_id" in x:
            out.append(("decision",x["decision_id"],x.get("actor_id"),x["outcome"]))
    return out,r["decision"]
def new_projection(r):
    out=[]
    # Attempt summaries are emitted before leaf decisions in the legacy projection.
    events=r["events"]
    for e in events:
        if e["event"]=="process_start" and e["process_id"]=="budget_approval":
            p=e["instance_path"]
            end=next(x for x in events if x["instance_path"]==p and x["event"]=="process_end")
            c=end["context"]
            out.append(("budget_attempt",c["actor"],c["limit"],end["end"]))
        if e["event"]=="decision":
            d=e["decision_id"]
            if d=="escalation_route": continue
            if d=="budget_outcome":
                p=e["instance_path"]
                end=next(x for x in events if x["instance_path"]==p and x["event"]=="process_end")
                if end["context"]["limit"] is None: continue
            out.append(("decision","corporate_readiness" if d=="corporate_readiness_direct" else d,e["actor_id"],e["outcome"]))
    result=r["result"]
    return out,"pending" if result["end"]=="pending" else result["context"]["dealOutcome"]
def compare(a,b):
    if old_projection(a)!=new_projection(b): raise ValueError("semantic trace mismatch")
def main():
    cases=0
    for amount,funds,day,tech,rem,actor in product((500000,500001,5000001),(False,True),("2026-06-01","2027-01-01"),(False,True),(False,True),("P1","P2")):
        a=legacy("legacy",dict(requirementsMet=tech,remediable=rem),dict(amount=amount,funds=funds,as_of=day),dict(initiator="P4",technical_expertise="P2",budget_approval="P3",deal_approval=actor))
        b=execute_authoritative("corporate_multilevel_universal",dict(technicalActor="P2",budgetActor="P3",dealActor=actor,initiator="P4",amount=amount,as_of=day,fundsAvailable=funds,technicalRequirementsMet=tech,remediable=rem))
        compare(a,b); cases+=1
    negatives=0
    for key,value in (("outcome","invalid"),("actor_id","P4")):
        bad=deepcopy(b); next(e for e in bad["events"] if e["event"]=="decision")[key]=value
        try: compare(a,bad)
        except ValueError: negatives+=1
        else: raise AssertionError("mutation accepted")
    print(json.dumps(dict(status="PASS",cases=cases,negative_tests=negatives,scope="ordered decisions, budget attempts and final outcome; not full node equivalence")))
if __name__=="__main__": main()
