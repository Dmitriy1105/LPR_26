"""Business oracle for the fixed demo organization; no DMN or legacy imports."""
import json
from itertools import product
from copy import deepcopy
from authority_execution_v1 import execute_authoritative as run
def oracle(technical,budget,deal,amount,day,funds,met,rem):
    tech="referred" if technical!="P2" else "positive" if met else "rework" if rem else "negative"
    attempts=[]
    actor=budget
    while True:
        limit={"P1":5000000,"P3":500000}.get(actor) if day.startswith("2026-") else None
        status="blocked" if limit is None else "rejected" if not funds else "approved" if amount<=limit else "escalated"
        attempts.append((actor,status))
        if status=="escalated" and actor=="P3": actor="P1"
        else: break
    readiness="pending" if tech in ("rework","referred") or status in ("blocked","escalated") else "ready" if tech=="positive" and status=="approved" else "not_ready"
    outcome=("approve" if deal=="P1" else "deny") if readiness=="ready" else None
    return tech,status,readiness,outcome,attempts
def projection(r):
    c=r["result"]["context"]
    paths={e["instance_path"]:e["process_id"] for e in r["events"] if e["event"]=="process_start"}
    attempts=[(e["context"]["actor"],e["end"]) for e in r["events"] if e["event"]=="process_end" and paths[e["instance_path"]]=="budget_approval"]
    return c["technicalStatus"],c["budgetStatus"],c["readiness"],c.get("dealOutcome"),attempts
def compare(r,expected):
    if projection(r)!=expected: raise ValueError(("semantic mismatch",projection(r),expected))
def main():
    count=0
    for t,b,d,amount,day,funds,met,rem in product(("P2","P4"),("P1","P3","P4"),("P1","P2"),(500000,500001,5000001),("2026-06-01","2027-01-01"),(False,True),(False,True),(False,True)):
        expected=oracle(t,b,d,amount,day,funds,met,rem)
        r=run("corporate_multilevel_universal",dict(technicalActor=t,budgetActor=b,dealActor=d,initiator="P4",amount=amount,as_of=day,fundsAvailable=funds,technicalRequirementsMet=met,remediable=rem))
        compare(r,expected); count+=1
    negatives=0
    for key in ("technicalStatus","budgetStatus","readiness","dealOutcome"):
        bad=deepcopy(r); bad["result"]["context"][key]="invalid"
        try: compare(bad,expected)
        except ValueError: negatives+=1
        else: raise AssertionError(key)
    print(json.dumps(dict(status="PASS",cases=count,negative_cases=negatives,scope="fixed organization, independent outcome and budget actor oracle")))
if __name__=="__main__": main()
