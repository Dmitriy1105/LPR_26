import json
from organization_engine_v1 import generate
from organizational_resilience_v1 import assess_network_resilience
def main():
    org=generate(seed=42,count=1)[0]; a,b,c,d=[p["id"] for p in org["people"][:4]]
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=c,subject_id="D1",source_ref="src1")]
    chain=dict(chain_id="CH1",event_id="EV1",participant_id=a,utterance_author_id=b,action_executor_id=c,addressee_id=d,confirming_source_ref="src1")
    result=assess_network_resilience(org,events,[chain],[a])
    assert result["status"]=="PASS" and result["removal_scenarios"][0]["removed_person_id"]==a
    assert result["edge_count"]==3 and result["person_count"]>=4
    try: assess_network_resilience(org,events,[chain],["UNKNOWN"])
    except ValueError: pass
    else: raise AssertionError("unknown critical person accepted")
    empty=assess_network_resilience(org,[],[],[])
    assert empty["edge_count"]==0 and empty["baseline_component_count"]==len(org["people"])
    print(json.dumps(dict(status="PASS",positive_cases=2,negative_cases=1)))
if __name__=="__main__": main()
