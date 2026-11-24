import json
from organization_engine_v1 import generate
from decision_confidence_risk_v1 import assess_decision_confidence
def main():
    org=generate(seed=42,count=1)[0]; a,b,c,d=[p["id"] for p in org["people"][:4]]
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=c,subject_id="DEAL-1",source_ref="minutes-1")]
    chain=dict(chain_id="CH1",event_id="EV1",participant_id=a,utterance_author_id=b,action_executor_id=c,addressee_id=d,confirming_source_ref="minutes-1")
    evidence=dict(source_ref="minutes-1",source_type="meeting_minutes",captured_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:02:00+08:00",recorded_by=c,content_sha256="a"*64)
    decision=dict(decision_id="D1",source_event_id="EV1",actor_id=c)
    good=assess_decision_confidence(org,events,[chain],[evidence],[decision])
    assert good["status"]=="PASS" and good["results"][0]["evidence_coverage_score"]==100 and good["results"][0]["risk_level"]=="LOW"
    missing=assess_decision_confidence(org,events,[],[],[decision])
    assert missing["status"]=="REVIEW_REQUIRED" and missing["results"][0]["risk_level"]=="HIGH"
    empty=assess_decision_confidence(org,events,[],[],[])
    assert empty["status"]=="EMPTY" and empty["probability_calibrated"] is False
    try: assess_decision_confidence(org,events,[chain],[evidence],[dict(decision,source_event_id="MISSING")])
    except ValueError: pass
    else: raise AssertionError("missing event accepted")
    print(json.dumps(dict(status="PASS",positive_cases=2,negative_cases=2,probability_calibrated=False)))
if __name__=="__main__": main()
