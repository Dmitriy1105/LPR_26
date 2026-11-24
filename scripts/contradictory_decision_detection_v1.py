"""Detect explicitly recorded conflicting outcomes for the same decision subject and scope."""
from collections import defaultdict
from datetime import datetime,timezone
from event_chronology_v1 import validate_events,chronology
from decision_authority_reconciliation_v1 import reconcile_decisions
def _instant(value):
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError("decided_at requires timezone")
    return dt.astimezone(timezone.utc)
def detect_contradictory_decisions(org,grants,delegations,events,decisions,window_days=90):
    validate_events(events)
    if not isinstance(window_days,int) or window_days<0: raise ValueError("window_days must be a non-negative integer")
    if not decisions:
        return {"schema_version":"1.0","status":"EMPTY","decision_count":0,"conflict_count":0,"conflicts":[],"unclassified_decision_ids":[],"authority_status":"NOT_ASSESSED","method":"explicit_outcome_conflict_detection_v1"}
    authority=reconcile_decisions(org,grants,delegations,events,decisions)
    event_by_id={e["event_id"]:e for e in chronology(events)}
    seen=set(); groups=defaultdict(list); unclassified=[]
    for d in decisions:
        required=("decision_id","actor_id","action","permission","decided_at","source_event_id")
        if any(k not in d for k in required): raise ValueError("missing decision field")
        if d["decision_id"] in seen: raise ValueError("duplicate decision id")
        seen.add(d["decision_id"])
        if d["source_event_id"] not in event_by_id: raise ValueError("decision source event missing")
        event=event_by_id[d["source_event_id"]]
        if event["actor_id"]!=d["actor_id"]: raise ValueError("decision actor differs from source event actor")
        if event["event_type"] not in ("decision","approval"): raise ValueError("source event is not a decision or approval")
        outcome=d.get("outcome",d.get("decision_value"))
        if not isinstance(outcome,str) or not outcome.strip():
            unclassified.append(d["decision_id"]); continue
        subject=event["subject_id"]
        key=(subject,d["action"],d["permission"])
        groups[key].append({"decision_id":d["decision_id"],"actor_id":d["actor_id"],"outcome":outcome.strip().casefold(),"decided_at":d["decided_at"],"source_event_id":event["event_id"],"source_ref":event["source_ref"]})
    conflicts=[]
    from datetime import timedelta
    for (subject,action,permission),rows in sorted(groups.items()):
        ordered=sorted(rows,key=lambda x:(_instant(x["decided_at"]),x["decision_id"]))
        for i,left in enumerate(ordered):
            for right in ordered[i+1:]:
                delta=_instant(right["decided_at"])-_instant(left["decided_at"])
                if delta>timedelta(days=window_days): break
                if left["outcome"]!=right["outcome"]:
                    conflicts.append({"subject_id":subject,"action":action,"permission":permission,"decision_ids":[left["decision_id"],right["decision_id"]],"outcomes":[left["outcome"],right["outcome"]],"actor_ids":[left["actor_id"],right["actor_id"]],"source_refs":[left["source_ref"],right["source_ref"]],"time_difference_days":round(delta.total_seconds()/86400,3),"status":"CONTRADICTION_REVIEW_REQUIRED"})
    return {"schema_version":"1.0","status":"REVIEW_REQUIRED" if conflicts or unclassified or authority["status"]!="PASS" else "PASS","decision_count":len(decisions),"conflict_count":len(conflicts),"conflicts":conflicts,"unclassified_decision_ids":sorted(unclassified),"authority_status":authority["status"],"unauthorized_decision_ids":authority["unauthorized_decisions"],"window_days":window_days,"method":"explicit_outcome_conflict_detection_v1","limitations":["Only explicit outcome or decision_value fields are compared; missing outcomes are reported as unclassified.","A different outcome may reflect a legitimate later revision, not necessarily an error; review chronology and supersession evidence.","The matching key uses event subject_id, action and permission; upstream subject identity must be reliable.","Authority reconciliation is reported separately and does not establish whether two outcomes are substantively contradictory."]}
