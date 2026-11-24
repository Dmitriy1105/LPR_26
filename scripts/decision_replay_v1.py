"""Deterministic, evidence-linked replay of recorded decisions at their historical dates."""
from decision_authority_reconciliation_v1 import reconcile_decisions
from event_chronology_v1 import validate_events,chronology
def replay_decisions(org,grants,delegations,events,decisions):
    validate_events(events)
    ordered=chronology(events)
    event_ids={e["event_id"] for e in ordered}
    seen=set(); replay=[]
    for d in sorted(decisions,key=lambda x:(x.get("decided_at",""),x.get("decision_id",""))):
        did=d.get("decision_id")
        if not isinstance(did,str) or not did.strip() or did in seen: raise ValueError("missing or duplicate decision id")
        seen.add(did)
        if d.get("source_event_id") not in event_ids: raise ValueError("decision source event missing")
        result=reconcile_decisions(org,grants,delegations,ordered,[d])
        row=result["results"][0]
        replay.append({"decision_id":did,"decided_at":d["decided_at"],"source_event_id":d["source_event_id"],"status":row["status"],"authorized":row["authorized"],"authority_source":row["authority_source"],"direct_reason":row["direct_result"]["reason"],"delegated_reason":row["delegated_result"]["reason"]})
    return {"schema_version":"1.0","status":"EMPTY" if not replay else ("PASS" if all(x["authorized"] for x in replay) else "REVIEW_REQUIRED"),"replayed_count":len(replay),"authorized_count":sum(x["authorized"] for x in replay),"review_required_count":sum(not x["authorized"] for x in replay),"replay":replay}
