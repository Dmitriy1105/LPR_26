import json
from organization_engine_v1 import generate
from multifactor_decision_maker_v1 import rank_decision_makers
def main():
    org=generate(seed=42,count=1)[0]; a,b,c,d=[p["id"] for p in org["people"][:4]]
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=c,subject_id="D1",source_ref="minutes")]
    chain=dict(chain_id="CH1",event_id="EV1",participant_id=a,utterance_author_id=b,action_executor_id=c,addressee_id=d,confirming_source_ref="minutes")
    grant=dict(grant_id="G1",org_id=org["id"],person_id=c,action="contract",permission="final_decision",valid_from="2026-01-01",valid_until="2027-01-01",source_ref="board-resolution")
    decision=dict(decision_id="D1",actor_id=c,action="contract",permission="final_decision",decided_at="2026-06-01",source_event_id="EV1")
    result=rank_decision_makers(org,events,[chain],[grant],[],[decision])
    assert result["status"]=="PASS" and result["candidate_count"]==len(org["people"])
    assert result["ranked_candidates"][0]["person_id"]==c
    assert abs(sum(result["weights"].values())-1)<1e-9
    no_decisions=rank_decision_makers(org,events,[chain])
    assert no_decisions["status"]=="REVIEW_REQUIRED" and no_decisions["authority_status"]=="NOT_ASSESSED"
    try: rank_decision_makers(org,events,[chain],weights={"participation":-1})
    except ValueError: pass
    else: raise AssertionError("invalid weights accepted")
    try: rank_decision_makers(org,events,[chain],weights={"formal_role":1})
    except ValueError: pass
    else: raise AssertionError("incomplete weights accepted")
    empty=rank_decision_makers(org,[],[])
    assert empty["candidate_count"]==len(org["people"]) and empty["status"]=="REVIEW_REQUIRED"
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=2)))
if __name__=="__main__": main()
