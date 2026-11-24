"""Reconcile recorded decisions with time-bounded direct/delegated authority evidence."""
from event_chronology_v1 import validate_events,chronology
from temporal_authority_v1 import authorize_at
from delegation_authority_v1 import authorize_delegated_at
def reconcile_decisions(org,grants,delegations,events,decisions):
    validate_events(events)
    ordered=chronology(events); event_by_id={e["event_id"]:e for e in ordered}
    rows=[]
    for d in decisions:
        required=("decision_id","actor_id","action","permission","decided_at","source_event_id")
        if any(k not in d for k in required): raise ValueError("missing decision field")
        if d["source_event_id"] not in event_by_id: raise ValueError("decision source event missing")
        e=event_by_id[d["source_event_id"]]
        if e["actor_id"]!=d["actor_id"]: raise ValueError("decision actor differs from source event actor")
        if e["event_type"] not in ("decision","approval"): raise ValueError("source event is not a decision or approval")
        direct=authorize_at(org,grants,d["actor_id"],d["action"],d["permission"],d["decided_at"],d.get("amount"))
        delegated=authorize_delegated_at(org,grants,delegations,d["actor_id"],d["action"],d["permission"],d["decided_at"],d.get("amount"))
        source="direct" if direct["authorized"] else ("delegated" if delegated["authorized"] else None)
        rows.append({"decision_id":d["decision_id"],"actor_id":d["actor_id"],"source_event_id":e["event_id"],"authorized":bool(source),"authority_source":source,"status":"AUTHORIZED" if source else "UNAUTHORIZED","direct_result":direct,"delegated_result":delegated})
    return {"schema_version":"1.0","status":"PASS" if all(x["authorized"] for x in rows) else "REVIEW_REQUIRED","decision_count":len(rows),"authorized_count":sum(x["authorized"] for x in rows),"unauthorized_decisions":[x["decision_id"] for x in rows if not x["authorized"]],"results":rows}
