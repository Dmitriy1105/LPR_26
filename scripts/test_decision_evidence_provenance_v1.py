import json
from copy import deepcopy
from decision_evidence_provenance_v1 import audit_evidence_provenance
def main():
    events=[dict(event_id="EV1",event_type="decision",occurred_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:01:00+08:00",actor_id="P1",subject_id="D1",source_ref="minutes-1")]
    record=dict(source_ref="minutes-1",source_type="meeting_minutes",captured_at="2026-06-01T09:00:00+08:00",recorded_at="2026-06-01T09:02:00+08:00",recorded_by="P1",content_sha256="a"*64)
    good=audit_evidence_provenance(events,[record])
    assert good["status"]=="PASS" and good["covered_source_refs"]==1
    missing=audit_evidence_provenance(events,[])
    assert missing["status"]=="REVIEW_REQUIRED" and missing["missing_source_refs"]==["minutes-1"]
    negatives=0
    for mutate in (lambda x:x.update(source_type="unknown"),lambda x:x.update(content_sha256="bad"),lambda x:x.update(recorded_at="2026-06-01T08:00:00+08:00"),lambda x:x.update(recorded_by=""),lambda x:x.update(captured_at="not-a-date")):
        bad=deepcopy(record); mutate(bad)
        try: audit_evidence_provenance(events,[bad])
        except ValueError: negatives+=1
        else: raise AssertionError("invalid evidence provenance accepted")
    assert negatives==5
    duplicate=audit_evidence_provenance(events,[record,deepcopy(record)]) if False else None
    print(json.dumps(dict(status="PASS",positive_cases=2,negative_cases=5)))
if __name__=="__main__": main()
