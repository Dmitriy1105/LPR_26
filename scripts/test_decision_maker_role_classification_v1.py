import json
from organization_engine_v1 import generate
from decision_maker_role_classification_v1 import classify_decision_maker_roles
def main():
    org=generate(seed=42,count=1)[0]; a,b,c,d=[p["id"] for p in org["people"][:4]]
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=c,subject_id="D1",source_ref="minutes")]
    chain=dict(chain_id="CH1",event_id="EV1",participant_id=a,utterance_author_id=b,action_executor_id=c,addressee_id=d,confirming_source_ref="minutes")
    grant=dict(grant_id="G1",org_id=org["id"],person_id=c,action="contract",permission="final_decision",valid_from="2026-01-01",valid_until="2027-01-01",source_ref="board-resolution")
    decision=dict(decision_id="D1",actor_id=c,action="contract",permission="final_decision",decided_at="2026-06-01",source_event_id="EV1")
    result=classify_decision_maker_roles(org,events,[chain],[grant],[],[decision])
    roles={x["person_id"]:x["role_class"] for x in result["classifications"]}
    assert result["status"]=="REVIEW_REQUIRED" or result["status"]=="PASS"
    assert roles[c]=="AUTHORIZED_DECISION_MAKER"
    assert all(x["human_review_required"] for x in result["classifications"])
    no_authority=classify_decision_maker_roles(org,events,[chain])
    roles2={x["person_id"]:x["role_class"] for x in no_authority["classifications"]}
    assert no_authority["authority_status"]=="NOT_ASSESSED"
    assert roles2[c]!="AUTHORIZED_DECISION_MAKER"
    empty=classify_decision_maker_roles(org,[],[])
    assert empty["classification_count"]==len(org["people"])
    try:
        classify_decision_maker_roles(org,events,[chain],weights={"formal_role":-1})
    except ValueError: pass
    else: raise AssertionError("invalid weights accepted")
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=1)))
if __name__=="__main__": main()
