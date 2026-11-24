import json
from nlp_decision_evidence_adapter_v1 import adapt_nlp_evidence
def main():
    signals=[{"signal_id":"S1","activity_id":"A1","segment_id":"A1:2","segment_index":2,"signal_type":"action","signal_text":"предложил согласовать сроки","evidence_ref":"nlp10:S1","role_context":"Руководитель проекта"},{"signal_id":"S2","activity_id":"A2","segment_id":"A2:2","segment_index":2,"signal_type":"risk","signal_text":"указал на риск задержки","evidence_ref":"nlp10:S2"}]
    truth=[{"activity_id":"A1","action_segment_index":2,"synthetic_action_text":"предложил согласовать сроки","actor_contact_id":None,"actor_identity_verified":False},{"activity_id":"A2","action_segment_index":2,"synthetic_action_text":"указал на риск задержки","actor_contact_id":"C7","actor_identity_verified":True}]
    result=adapt_nlp_evidence(signals,truth,{"A1":["C1","C2"],"A2":["C7"]})
    rows={x["signal_id"]:x for x in result["signals"]}
    assert result["status"]=="PASS" and result["signal_count"]==2
    assert rows["S1"]["actor_contact_id"] is None and not rows["S1"]["eligible_for_person_level_decision_chain"]
    assert rows["S1"]["attribution_status"]=="participant_candidates_only"
    assert rows["S2"]["actor_contact_id"]=="C7" and rows["S2"]["eligible_for_person_level_decision_chain"]
    assert rows["S1"]["role_context_is_person_attribution"] is False
    empty=adapt_nlp_evidence([])
    assert empty["status"]=="EMPTY"
    try: adapt_nlp_evidence(signals+[dict(signals[0])])
    except ValueError: pass
    else: raise AssertionError("duplicate signal id accepted")
    try: adapt_nlp_evidence([{"signal_id":"S3"}])
    except ValueError: pass
    else: raise AssertionError("incomplete signal accepted")
    print(json.dumps({"status":"PASS","positive_cases":4,"negative_cases":2}))
if __name__=="__main__":main()
