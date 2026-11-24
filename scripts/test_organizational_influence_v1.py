import json
from copy import deepcopy
from organization_engine_v1 import generate
from organizational_influence_v1 import build_influence_graph,detect_missing_participants
def main():
    org=generate(seed=42,count=1)[0]; a,b,c,d=[p["id"] for p in org["people"][:4]]
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id=c,subject_id="D1",source_ref="minutes")]
    chain=dict(chain_id="CH1",event_id="EV1",participant_id=a,utterance_author_id=b,action_executor_id=c,addressee_id=d,confirming_source_ref="minutes")
    graph=build_influence_graph(org,events,[chain])
    assert graph["status"]=="PASS" and graph["edge_count"]==3
    assert any(e["source"]==a and e["target"]==b for e in graph["edges"])
    assert any(e["source"]==c and e["target"]==d for e in graph["edges"])
    coverage=detect_missing_participants(org,events,[chain],expected_participant_ids=[a,b])
    assert coverage["status"]=="PASS" and coverage["coverage_ratio"]==0.5
    missing=detect_missing_participants(org,events+[dict(events[0],event_id="EV2")],[chain],expected_participant_ids=[a])
    assert missing["status"]=="REVIEW_REQUIRED" and missing["events_without_attribution"]==["EV2"]
    try: build_influence_graph(org,events,[dict(chain,participant_id="UNKNOWN")])
    except ValueError: pass
    else: raise AssertionError("unknown participant accepted")
    # Deterministic output independent of chain ordering.
    assert graph==build_influence_graph(org,list(reversed(events)),[chain])
    print(json.dumps(dict(status="PASS",positive_cases=3,negative_cases=2,edges=3)))
if __name__=="__main__": main()
