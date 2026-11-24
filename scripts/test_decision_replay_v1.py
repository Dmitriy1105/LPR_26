import json
from organization_engine_v1 import generate
from decision_replay_v1 import replay_decisions
def main():
    org=generate(seed=42,count=1)[0]; actor=org["people"][0]["id"]
    grants=[dict(grant_id="G1",org_id=org["id"],person_id=actor,action="contract",permission="final_decision",valid_from="2026-01-01",valid_until="2027-01-01",source_ref="board-resolution")]
    events=[
      dict(event_id="EV2",event_type="approval",occurred_at="2026-06-02T09:00:00+08:00",recorded_at="2026-06-02T09:01:00+08:00",actor_id=actor,subject_id="C2",source_ref="approval"),
      dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=actor,subject_id="C1",source_ref="minutes")]
    decisions=[
      dict(decision_id="D2",actor_id=actor,action="contract",permission="final_decision",decided_at="2026-06-02",source_event_id="EV2"),
      dict(decision_id="D1",actor_id=actor,action="contract",permission="final_decision",decided_at="2026-06-01",source_event_id="EV1")]
    first=replay_decisions(org,grants,[],events,decisions)
    second=replay_decisions(org,grants,[],list(reversed(events)),list(reversed(decisions)))
    assert first==second and first["status"]=="PASS" and first["replayed_count"]==2
    no_grant=replay_decisions(org,[],[],events,decisions)
    assert no_grant["status"]=="REVIEW_REQUIRED" and no_grant["review_required_count"]==2
    assert replay_decisions(org,grants,[],events,[])["status"]=="EMPTY"
    try: replay_decisions(org,grants,[],events,decisions+[decisions[0]])
    except ValueError: pass
    else: raise AssertionError("duplicate decision id accepted")
    try: replay_decisions(org,grants,[],events,[dict(decisions[0],source_event_id="MISSING")])
    except ValueError: pass
    else: raise AssertionError("missing source event accepted")
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=2)))
if __name__=="__main__": main()
