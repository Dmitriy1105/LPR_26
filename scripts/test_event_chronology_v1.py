import json
from copy import deepcopy
from event_chronology_v1 import validate_events,chronology,events_as_of
def fixtures():
    return [dict(event_id="E1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:05:00+08:00",actor_id="P1",subject_id="D1",source_ref="minutes-1",correlation_id="C1"),dict(event_id="E2",event_type="approval",occurred_at="2026-06-01T02:00:00Z",recorded_at="2026-06-01T02:10:00Z",actor_id="P2",subject_id="D1",source_ref="approval-1",causation_id="E1",correlation_id="C1")]
def main():
    e=fixtures(); assert validate_events(e)
    assert [x["event_id"] for x in chronology(e)]==["E1","E2"]
    assert len(events_as_of(e,"2026-06-01T02:05:00Z","recorded_at"))==1
    assert len(events_as_of(e,"2026-06-01T02:00:00Z","occurred_at"))==2
    negatives=0
    for mutate in (lambda x:x[0].update(event_id=""),lambda x:x[0].update(event_type="unknown"),lambda x:x[0].update(occurred_at="2026-06-01T09:00:00"),lambda x:x[0].update(recorded_at="2026-06-01T08:00:00+08:00"),lambda x:x[1].update(causation_id="missing"),lambda x:x[0].update(causation_id="E2"),lambda x:x[1].update(causation_id="E2"),lambda x:x.append(x[0]),lambda x:x[0].update(actor_id=""),lambda x:x[0].update(source_ref="")):
        bad=deepcopy(e); mutate(bad)
        try: validate_events(bad)
        except ValueError: negatives+=1
        else: raise AssertionError("invalid chronology event accepted")
    print(json.dumps(dict(status="PASS",positive_cases=4,negative_cases=negatives)))
if __name__=="__main__": main()
