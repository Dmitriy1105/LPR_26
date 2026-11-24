import json
from copy import deepcopy
from organization_engine_v1 import generate
from decision_attribution_chain_v1 import validate_attribution_chain
def main():
    org=generate(seed=42,count=1)[0]; a,b,c,d=[p["id"] for p in org["people"][:4]]
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=c,subject_id="DEAL-1",source_ref="minutes-1")]
    chain=dict(chain_id="CH1",event_id="EV1",participant_id=a,utterance_author_id=b,action_executor_id=c,addressee_id=d,confirming_source_ref="minutes-1")
    good=validate_attribution_chain(org,events,[chain])
    assert good["status"]=="PASS" and good["complete_count"]==1
    partial=dict(chain); partial.pop("addressee_id")
    review=validate_attribution_chain(org,events,[partial])
    assert review["status"]=="REVIEW_REQUIRED" and review["incomplete_chain_ids"]==["CH1"]
    negatives=0
    for mutate in (lambda x:x.update(action_executor_id=a),lambda x:x.update(confirming_source_ref="wrong"),lambda x:x.update(participant_id="UNKNOWN"),lambda x:x.update(event_id="MISSING"),lambda x:x.update(chain_id="")):
        bad=deepcopy(chain); mutate(bad)
        try: validate_attribution_chain(org,events,[bad])
        except ValueError: negatives+=1
        else: raise AssertionError("invalid attribution chain accepted")
    assert negatives==5
    print(json.dumps(dict(status="PASS",positive_cases=2,negative_cases=5)))
if __name__=="__main__": main()
