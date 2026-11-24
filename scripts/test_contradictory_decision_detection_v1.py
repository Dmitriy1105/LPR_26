import json
from organization_engine_v1 import generate
from contradictory_decision_detection_v1 import detect_contradictory_decisions
def main():
    org=generate(seed=42,count=1)[0]; a,b=org["people"][0]["id"],org["people"][1]["id"]
    grants=[dict(grant_id="G1",org_id=org["id"],person_id=a,action="contract",permission="final_decision",valid_from="2026-01-01",valid_until="2027-01-01",source_ref="board-resolution")]
    events=[
      dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=a,subject_id="DEAL-1",source_ref="minutes-1"),
      dict(event_id="EV2",event_type="decision",occurred_at="2026-06-10T09:00:00+08:00",recorded_at="2026-06-10T09:01:00+08:00",actor_id=a,subject_id="DEAL-1",source_ref="minutes-2"),
      dict(event_id="EV3",event_type="decision",occurred_at="2026-06-11T09:00:00+08:00",recorded_at="2026-06-11T09:01:00+08:00",actor_id=a,subject_id="DEAL-2",source_ref="minutes-3")]
    base=dict(actor_id=a,action="contract",permission="final_decision")
    decisions=[dict(base,decision_id="D1",decided_at="2026-06-01T09:00:00+08:00",source_event_id="EV1",outcome="approved"),dict(base,decision_id="D2",decided_at="2026-06-10T09:00:00+08:00",source_event_id="EV2",outcome="rejected"),dict(base,decision_id="D3",decided_at="2026-06-11T09:00:00+08:00",source_event_id="EV3",outcome="approved")]
    result=detect_contradictory_decisions(org,grants,[],events,decisions)
    assert result["conflict_count"]==1 and result["conflicts"][0]["decision_ids"]==["D1","D2"]
    assert result["status"]=="REVIEW_REQUIRED"
    missing=detect_contradictory_decisions(org,grants,[],events,[dict(decisions[0])])
    assert missing["status"]=="REVIEW_REQUIRED" and missing["unclassified_decision_ids"]==["D1"]
    empty=detect_contradictory_decisions(org,grants,[],[],[])
    assert empty["status"]=="EMPTY"
    outside=detect_contradictory_decisions(org,grants,[],events,[decisions[0],decisions[1]],window_days=2)
    assert outside["conflict_count"]==0
    try: detect_contradictory_decisions(org,grants,[],events,decisions,window_days=-1)
    except ValueError: pass
    else: raise AssertionError("negative window accepted")
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=2)))
if __name__=="__main__": main()
