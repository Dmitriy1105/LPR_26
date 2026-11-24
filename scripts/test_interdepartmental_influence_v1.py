import json
from organization_engine_v1 import generate
from interdepartmental_influence_v1 import analyze_interdepartmental_influence
def main():
    org=generate(seed=42,count=1)[0]; by_dept={u["department"]:next(p["id"] for p in org["people"] if p["unit"]==u["id"]) for u in org["units"] if u["department"]!="headquarters"}
    sales,finance,technical,security,infosec=[by_dept[x] for x in ("sales","finance","technical","security","information_security")]
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=finance,subject_id="D1",source_ref="minutes")]
    chain=dict(chain_id="CH1",event_id="EV1",participant_id=sales,utterance_author_id=technical,action_executor_id=finance,addressee_id=security,confirming_source_ref="minutes")
    result=analyze_interdepartmental_influence(org,events,[chain])
    assert result["status"]=="PASS" and result["cross_department_pair_count"]==6
    assert result["cross_department_interaction_count"]==6
    assert "information_security" in result["departments_without_observed_interaction"]
    missing=analyze_interdepartmental_influence(org,events,[])
    assert missing["status"]=="REVIEW_REQUIRED" and missing["unattributed_event_ids"]==["EV1"]
    empty=analyze_interdepartmental_influence(org,[],[])
    assert empty["cross_department_pair_count"]==0 and empty["status"]=="PASS"
    bad=dict(chain,participant_id="UNKNOWN")
    try: analyze_interdepartmental_influence(org,events,[bad])
    except ValueError: pass
    else: raise AssertionError("unknown person accepted")
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=1,cross_department_pairs=6)))
if __name__=="__main__": main()
