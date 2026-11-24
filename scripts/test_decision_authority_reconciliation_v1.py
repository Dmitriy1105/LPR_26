import json
from copy import deepcopy
from organization_engine_v1 import generate
from decision_authority_reconciliation_v1 import reconcile_decisions
def main():
    org=generate(seed=42,count=1)[0]; a,b=org["people"][0]["id"],org["people"][1]["id"]
    grants=[dict(grant_id="G1",org_id=org["id"],person_id=a,action="contract",permission="final_decision",valid_from="2026-01-01",valid_until="2027-01-01",source_ref="board-resolution")]
    delegations=[]
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=a,subject_id="C1",source_ref="minutes")]
    decisions=[dict(decision_id="D1",actor_id=a,action="contract",permission="final_decision",decided_at="2026-06-01",source_event_id="EV1")]
    good=reconcile_decisions(org,grants,delegations,events,decisions)
    assert good["status"]=="PASS" and good["authorized_count"]==1
    # actor/source mismatch must be rejected rather than silently reconciled
    negatives=0
    for bad_decisions,bad_events in (([dict(decisions[0],actor_id=b)],events),([dict(decisions[0],source_event_id="MISSING")],events),([dict(decisions[0],permission="approve")],events),([dict(decisions[0],decided_at="2025-01-01")],events)):
        try: reconcile_decisions(org,grants,delegations,bad_events,bad_decisions)
        except ValueError: negatives+=1
        else: raise AssertionError("invalid decision evidence accepted")
    unauthorized=reconcile_decisions(org,grants,delegations,events,[dict(decisions[0],actor_id=a,action="payment")])
    assert unauthorized["status"]=="REVIEW_REQUIRED" and unauthorized["authorized_count"]==0
    print(json.dumps(dict(status="PASS",positive_cases=2,negative_cases=negatives)))
if __name__=="__main__": main()
