import json
from organization_engine_v1 import generate
from customer_relationship_dynamics_v1 import analyze_relationship_dynamics
def main():
    org=generate(seed=42,count=1)[0]; a,b,c,d=[p["id"] for p in org["people"][:4]]
    events=[
      dict(event_id="EV2",event_type="communication",occurred_at="2026-07-01T09:00:00+08:00",recorded_at="2026-07-01T09:01:00+08:00",actor_id=c,subject_id="CUSTOMER-1",source_ref="src2"),
      dict(event_id="EV1",event_type="communication",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=b,subject_id="CUSTOMER-1",source_ref="src1"),
      dict(event_id="EV3",event_type="decision",occurred_at="2026-07-02T09:00:00+08:00",recorded_at="2026-07-02T09:01:00+08:00",actor_id=a,subject_id="OTHER-CUSTOMER",source_ref="src3")]
    chains=[
      dict(chain_id="CH1",event_id="EV1",participant_id=a,utterance_author_id=b,action_executor_id=b,addressee_id=c,confirming_source_ref="src1"),
      dict(chain_id="CH2",event_id="EV2",participant_id=a,utterance_author_id=b,action_executor_id=c,addressee_id=d,confirming_source_ref="src2"),
      dict(chain_id="CH3",event_id="EV3",participant_id=a,utterance_author_id=b,action_executor_id=a,addressee_id=d,confirming_source_ref="src3")]
    result=analyze_relationship_dynamics(org,events,chains,"CUSTOMER-1")
    assert result["status"]=="PASS" and result["event_count"]==2 and result["active_month_count"]==2
    assert result["participant_count"]==4 and result["first_activity_month"]=="2026-06"
    missing=analyze_relationship_dynamics(org,events,chains[:1],"CUSTOMER-1")
    assert missing["status"]=="REVIEW_REQUIRED" and missing["unattributed_event_ids"]==["EV2"]
    all_customers=analyze_relationship_dynamics(org,events,chains)
    assert all_customers["event_count"]==3 and all_customers["active_month_count"]==2
    empty=analyze_relationship_dynamics(org,[],[])
    assert empty["status"]=="PASS" and empty["timeline"]==[]
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=1)))
if __name__=="__main__": main()
