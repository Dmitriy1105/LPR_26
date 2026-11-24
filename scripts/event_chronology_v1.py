"""Auditable event chronology: occurrence time is distinct from ingestion time."""
from datetime import datetime, timezone
EVENT_TYPES=("decision","approval","delegation","task_assigned","task_completed","communication","org_change")
def _instant(value,name):
    if not isinstance(value,str): raise ValueError(name+" must be ISO-8601 string")
    try: dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise ValueError("invalid "+name) from exc
    if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError(name+" must include timezone")
    return dt.astimezone(timezone.utc)
def validate_events(events):
    ids=set()
    for e in events:
        required=("event_id","event_type","occurred_at","recorded_at","source_ref")
        if any(k not in e for k in required): raise ValueError("missing event field")
        for k in ("event_id","source_ref"):
            if not isinstance(e[k],str) or not e[k].strip(): raise ValueError("empty "+k)
        if e["event_id"] in ids: raise ValueError("duplicate event id")
        ids.add(e["event_id"])
        if e["event_type"] not in EVENT_TYPES: raise ValueError("unknown event type")
        occurred=_instant(e["occurred_at"],"occurred_at")
        recorded=_instant(e["recorded_at"],"recorded_at")
        if recorded<occurred: raise ValueError("recorded_at precedes occurred_at")
        if not isinstance(e.get("actor_id"),str) or not e["actor_id"].strip(): raise ValueError("missing actor")
        if not isinstance(e.get("subject_id"),str) or not e["subject_id"].strip(): raise ValueError("missing subject")
        if e.get("causation_id") is not None and not isinstance(e["causation_id"],str): raise ValueError("invalid causation id")
        if e.get("correlation_id") is not None and not isinstance(e["correlation_id"],str): raise ValueError("invalid correlation id")
    by_id={e["event_id"]:e for e in events}
    for e in events:
        parent=e.get("causation_id")
        if parent is not None and parent not in by_id: raise ValueError("unknown causation event")
        visited=set(); current=e["event_id"]
        while current is not None:
            if current in visited: raise ValueError("causation cycle")
            visited.add(current)
            current=by_id[current].get("causation_id")
    return True
def chronology(events):
    validate_events(events)
    # Occurrence time is primary; recorded time and ID provide deterministic tie-breaks.
    return sorted(events,key=lambda e:(_instant(e["occurred_at"],"occurred_at"),_instant(e["recorded_at"],"recorded_at"),e["event_id"]))
def events_as_of(events,instant,clock="occurred_at"):
    if clock not in ("occurred_at","recorded_at"): raise ValueError("unsupported clock")
    cutoff=_instant(instant,"instant")
    return [e for e in chronology(events) if _instant(e[clock],clock)<=cutoff]
