import json
from organization_engine_v1 import generate
from missing_decision_makers_v1 import detect_missing_decision_makers
def main():
    org=generate(seed=42,count=1)[0]; a,b,c,d=[p["id"] for p in org["people"][:4]]
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=c,subject_id="D1",source_ref="minutes")]
    chain=dict(chain_id="CH1",event_id="EV1",participant_id=a,utterance_author_id=b,action_executor_id=c,addressee_id=d,confirming_source_ref="minutes")
    roster=[dict(person_id=x,expected_role=org["people"][i]["role"],required=True) for i,x in enumerate([a,b,c,d])]
    good=detect_missing_decision_makers(org,events,[chain],roster)
    assert good["status"]=="PASS" and good["coverage_ratio"]==1.0
    missing=detect_missing_decision_makers(org,events,[dict(chain,addressee_id=a)],[dict(roster[3],required=True)])
    assert missing["status"]=="REVIEW_REQUIRED" and missing["missing_required_person_ids"]==[d]
    optional=detect_missing_decision_makers(org,events,[dict(chain,addressee_id=a)],[dict(roster[3],required=False)])
    assert optional["status"]=="PASS" and optional["missing_optional_person_ids"]==[d]
    empty=detect_missing_decision_makers(org,[],[],[])
    assert empty["status"]=="PASS" and empty["coverage_ratio"]==1.0
    try: detect_missing_decision_makers(org,events,[chain],roster+[roster[0]])
    except ValueError: pass
    else: raise AssertionError("duplicate roster entry accepted")
    try: detect_missing_decision_makers(org,events,[chain],[dict(person_id="UNKNOWN",required=True)])
    except ValueError: pass
    else: raise AssertionError("unknown expected person accepted")
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=2)))
if __name__=="__main__": main()
