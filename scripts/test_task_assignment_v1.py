import json
from task_assignment_v1 import assign,complete
def main():
    base=dict(instance="I1",process="technical_expertise",node="technical_review",initiator="P4",assigner="P1",assignee="P2",issued_at="2026-06-01T09:00:00",due_at="2026-06-02T09:00:00")
    cases=0
    for p,n,a in (("technical_expertise","technical_review","P2"),("budget_approval","financial_review","P3"),("deal_approval","complete","P2"),("deal_approval","complete","P3")):
        r=assign(**{**base,"process":p,"node":n,"assignee":a})
        assert r["actual_actor_id"] is None and not r["decision_authority_transferred"]
        c=complete(r,a,"2026-06-01T10:00:00")
        assert c["actual_actor_id"]==a and c["status"]=="completed"
        cases+=1
    r=assign(**base); c=complete(r,"P2","2026-06-01T10:00:00")
    negatives=0
    tests=[lambda:assign(**{**base,**patch}) for patch in (dict(assigner="P4"),dict(assignee="P3"),dict(initiator="missing"),dict(node="missing"),dict(due_at=base["issued_at"]),dict(assignee="P1"))]
    tests += [lambda:complete(r,"P3","2026-06-01T10:00:00"),lambda:complete(r,"P2","2026-06-03T10:00:00"),lambda:complete(r,"P2","2026-05-31T10:00:00"),lambda:complete(c,"P2","2026-06-01T10:00:00")]
    for fn in tests:
        try: fn()
        except ValueError: negatives+=1
        else: raise AssertionError("invalid assignment accepted")
    print(json.dumps(dict(status="PASS",cases=cases,negative_tests=negatives)))
if __name__=="__main__": main()
