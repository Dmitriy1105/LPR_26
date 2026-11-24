"""Authority and actor regression checks for the current organization fixture."""
import json
from organization_decision_audit import simulate
from budget_escalation_v4 import escalate
def main():
    passed=[]
    for p,actor,inputs,expected,grant in [
        ("deal_approval","P1",dict(requirementsMet=True,revisionAllowed=False),"end",True),
        ("deal_approval","P2",dict(requirementsMet=True,revisionAllowed=False),"blocked",False),
        ("deal_approval","P3",dict(requirementsMet=True,revisionAllowed=False),"blocked",False),
        ("budget_approval","P3",dict(fundsAvailable=True,withinLimit=True),"approved",True),
        ("budget_approval","P2",dict(fundsAvailable=True,withinLimit=True),"blocked",False),
        ("technical_expertise","P2",dict(requirementsMet=True,remediable=False),"positive",True),
        ("technical_expertise","P1",dict(requirementsMet=True,remediable=False),"referred",False)]:
        r=simulate(p,"authority-"+str(len(passed)),"P4",actor,inputs)
        assert r["end"]==expected and r["initiator_id"]=="P4"
        for e in r["records"]:
            if "decision_id" in e:
                assert e["actor_id"]==actor and e["authority_source"]["granted"] is grant
            if e["node_id"] in {"deny","refer_expert"}:
                assert e["actor_id"] is None and e["subject_id"]==actor
            if e["node_id"] in {"approve","reject","recommend_accept"}:
                assert grant and e["actor_id"]==actor
        passed.append(p+":"+actor)
    for amount,day,outcome,actors in [
        (500000,"2026-01-01","approved",["P3"]),
        (500001,"2026-12-31","approved",["P3","P1"]),
        (5000000,"2026-06-01","approved",["P3","P1"]),
        (5000001,"2026-06-01","unresolved_limit",["P3","P1"]),
        (100,"2025-12-31","no_active_grant",["P3"]),
        (100,"2027-01-01","no_active_grant",["P3"])]:
        r=escalate("limit-"+str(len(passed)),amount,True,day)
        assert r["outcome"]==outcome and [a["actor"] for a in r["attempts"]]==actors
        passed.append(str(amount)+":"+day)
    for initiator,actor,inputs in [("unknown","P1",{}),("P4","unknown",{}),("P4","P2",{"authorized":True})]:
        try: simulate("deal_approval","invalid",initiator,actor,inputs)
        except ValueError: passed.append("reject:"+initiator+":"+actor)
        else: raise AssertionError("invalid authority accepted")
    print(json.dumps(dict(status="PASS",count=len(passed),tests=passed),indent=2))
if __name__=="__main__": main()
