import json
from organization_engine_v1 import generate
from decision_maker_evolution_v1 import analyze_decision_maker_evolution
def main():
    org=generate(seed=42,count=1)[0]; a,b,c,d=[p["id"] for p in org["people"][:4]]
    events=[
      dict(event_id="EV1",event_type="communication",occurred_at="2026-05-01T09:00:00+08:00",recorded_at="2026-05-01T09:01:00+08:00",actor_id=a,subject_id="C1",source_ref="s1"),
      dict(event_id="EV2",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=a,subject_id="C1",source_ref="s2"),
      dict(event_id="EV3",event_type="communication",occurred_at="2026-06-02T09:00:00+08:00",recorded_at="2026-06-02T09:01:00+08:00",actor_id=b,subject_id="C1",source_ref="s3")]
    chains=[
      dict(chain_id="CH1",event_id="EV1",participant_id=a,utterance_author_id=a,action_executor_id=a,addressee_id=d,confirming_source_ref="s1"),
      dict(chain_id="CH2",event_id="EV2",participant_id=a,utterance_author_id=b,action_executor_id=a,addressee_id=d,confirming_source_ref="s2"),
      dict(chain_id="CH3",event_id="EV3",participant_id=b,utterance_author_id=b,action_executor_id=b,addressee_id=d,confirming_source_ref="s3")]
    result=analyze_decision_maker_evolution(org,events,chains,"C1")
    rows={x["person_id"]:x for x in result["signals"]}
    assert result["status"]=="PASS" and rows[a]["trend"]=="INCREASING"
    assert rows[b]["signal"]=="EMERGING_PARTICIPATION"
    assert rows[c]["signal"]=="INSUFFICIENT_EVIDENCE"
    missing=analyze_decision_maker_evolution(org,events,chains[:1],"C1")
    assert missing["status"]=="REVIEW_REQUIRED" and missing["unattributed_event_ids"]==["EV2","EV3"]
    one_month=analyze_decision_maker_evolution(org,events[:1],chains[:1],"C1")
    assert one_month["status"]=="REVIEW_REQUIRED"
    empty=analyze_decision_maker_evolution(org,[],[])
    assert empty["observation_months"]==[] and empty["status"]=="REVIEW_REQUIRED"
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=2)))
if __name__=="__main__": main()
