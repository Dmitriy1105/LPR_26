"""Explicit equivalence checks between HR change events and physical chronology entries."""
from datetime import date,datetime
from event_chronology_v1 import validate_events as validate_chronology,chronology
from organizational_changes_v1 import validate_events as validate_org_events
def _utc_date(value):
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    return dt.date().isoformat()
def audit_journal_equivalence(org,org_events,physical_events,decision_traces=None):
    validate_org_events(org,org_events); validate_chronology(physical_events)
    decision_traces=decision_traces or []
    org_by_id={e["event_id"]:e for e in org_events}
    physical_by_source={}
    for e in physical_events:
        source_id=e.get("source_event_id")
        if source_id is not None:
            if source_id in physical_by_source: raise ValueError("duplicate physical representation for source event")
            physical_by_source[source_id]=e
    missing=[]; mismatches=[]; matched=[]
    for oid,oe in org_by_id.items():
        pe=physical_by_source.get(oid)
        if pe is None:
            missing.append(oid); continue
        payload=pe.get("event_payload")
        expected={"kind":oe["kind"],"person_id":oe["person_id"],"effective_date":oe["effective_date"],"source_ref":oe["source_ref"]}
        if pe.get("event_type")!="org_change" or pe.get("subject_id")!=oe["person_id"] or payload!=expected or _utc_date(pe["occurred_at"])!=oe["effective_date"]:
            mismatches.append({"source_event_id":oid,"physical_event_id":pe["event_id"]})
        else: matched.append(oid)
    orphaned=sorted(set(physical_by_source)-set(org_by_id))
    trace_missing=[]
    physical_ids={e["event_id"] for e in physical_events}
    for index,trace in enumerate(decision_traces):
        if not isinstance(trace,dict) or not isinstance(trace.get("event_ids"),list): raise ValueError("invalid decision trace")
        absent=[eid for eid in trace["event_ids"] if eid not in physical_ids]
        if absent: trace_missing.append({"trace_index":index,"missing_event_ids":absent})
    return {"schema_version":"1.0","status":"PASS" if not (missing or mismatches or orphaned or trace_missing) else "FAIL","organization_events":len(org_events),"physical_events":len(physical_events),"matched":len(matched),"missing_physical_events":missing,"mismatches":mismatches,"orphaned_physical_events":orphaned,"decision_trace_gaps":trace_missing,"physical_chronology_order":[e["event_id"] for e in chronology(physical_events)]}
