import json
from authority_execution_v1 import execute_authoritative as run
def main():
    cases=[]
    for actor in ("P1","P2","P3","P4"):
        for pid,extra,expected in [
            ("deal_approval",dict(requirementsMet=True,revisionAllowed=False),"end" if actor=="P1" else "blocked"),
            ("technical_expertise",dict(requirementsMet=True,remediable=False),"positive" if actor=="P2" else "referred"),
            ("budget_approval",dict(amount=100,as_of="2026-06-01",fundsAvailable=True),"approved" if actor in ("P1","P3") else "blocked")]:
            inputs=dict(actor=actor,initiator="P4",**extra)
            r=run(pid,inputs)
            assert r["result"]["end"]==expected,(pid,actor,r["result"]["end"])
            assert r==run(pid,inputs)
            cases.append([pid,actor,expected])
    for amount,day,expected in [(500000,"2026-01-01","approved"),(500001,"2026-12-31","approved"),(5000001,"2026-06-01","escalated"),(100,"2027-01-01","blocked")]:
        r=run("budget_escalation_universal",dict(actor="P3",initiator="P4",amount=amount,as_of=day,fundsAvailable=True))
        assert r["result"]["context"]["budgetStatus"]==expected
        cases.append(["escalation",amount,expected])
    for actor in ("P1","P2"):
        r=run("corporate_multilevel_universal",dict(technicalActor="P2",budgetActor="P3",dealActor=actor,initiator="P4",amount=500001,as_of="2026-06-01",fundsAvailable=True,technicalRequirementsMet=True,remediable=False))
        assert r["result"]["context"]["dealOutcome"]==("approve" if actor=="P1" else "deny")
        cases.append(["corporate",actor])
    negatives=0
    base=dict(actor="P2",initiator="P4",requirementsMet=True,revisionAllowed=False)
    for patch in ({"authorized":True},{"actor":"unknown"},{"initiator":"unknown"},{"competent":True},{"withinLimit":True}):
        try: run("deal_approval",{**base,**patch})
        except ValueError: negatives+=1
        else: raise AssertionError("invalid input accepted")
    print(json.dumps(dict(status="PASS",cases=cases,negative_tests=negatives)))
if __name__=="__main__": main()
