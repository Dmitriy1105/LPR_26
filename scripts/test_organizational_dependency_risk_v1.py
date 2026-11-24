import json
from organization_engine_v1 import generate
from organizational_dependency_risk_v1 import assess_dependency_risk
def main():
    org=generate(seed=42,count=1)[0]; people=[p["id"] for p in org["people"][:5]]
    a,b,c,d,e=people
    events=[dict(event_id=f"EV{i}",event_type="decision",occurred_at=f"2026-06-0{i}T09:00:00+08:00",recorded_at=f"2026-06-0{i}T09:01:00+08:00",actor_id=a,subject_id=f"D{i}",source_ref=f"src-{i}") for i in range(1,4)]
    chains=[dict(chain_id="C1",event_id="EV1",participant_id=a,utterance_author_id=a,action_executor_id=a,addressee_id=b,confirming_source_ref="src-1"),dict(chain_id="C2",event_id="EV2",participant_id=a,utterance_author_id=a,action_executor_id=a,addressee_id=c,confirming_source_ref="src-2"),dict(chain_id="C3",event_id="EV3",participant_id=a,utterance_author_id=a,action_executor_id=a,addressee_id=d,confirming_source_ref="src-3")]
    result=assess_dependency_risk(org,events,chains)
    assert result["status"]=="PASS" and result["top_person"]["person_id"]==a and result["heuristic_risk_level"]=="HIGH"
    assert result["event_coverage_after_top_person_removal"]==0.0
    missing=assess_dependency_risk(org,events[:2],chains[:1])
    assert missing["status"]=="REVIEW_REQUIRED" and missing["unattributed_event_ids"]==["EV2"]
    empty=assess_dependency_risk(org,[],[])
    assert empty["heuristic_risk_level"]=="LOW" and empty["calibrated_risk_probability"] is False
    try: assess_dependency_risk(org,events,chains,0.5,0.5)
    except ValueError: pass
    else: raise AssertionError("invalid thresholds accepted")
    print(json.dumps(dict(status="PASS",positive_cases=2,negative_cases=2)))
if __name__=="__main__": main()
