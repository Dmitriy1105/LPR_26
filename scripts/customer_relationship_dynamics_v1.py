"""Temporal customer-relationship indicators from timestamped CRM events and attribution chains."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from event_chronology_v1 import validate_events,chronology
from decision_attribution_chain_v1 import validate_attribution_chain
ROLES=("participant_id","utterance_author_id","action_executor_id","addressee_id")
def _month(value):
    dt=datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
    return dt.strftime("%Y-%m")
def analyze_relationship_dynamics(org,events,chains,customer_id=None):
    validate_events(events); validate_attribution_chain(org,events,chains)
    event_by_id={e["event_id"]:e for e in events}
    people={p["id"]:p for p in org.get("people",[])}
    selected=[e for e in chronology(events) if customer_id is None or e["subject_id"]==customer_id]
    selected_ids={e["event_id"] for e in selected}
    relevant=[c for c in chains if c["event_id"] in selected_ids]
    by_month=defaultdict(lambda:{"event_count":0,"event_types":Counter(),"participants":set(),"source_refs":set()})
    for e in selected:
        row=by_month[_month(e["occurred_at"])]
        row["event_count"]+=1; row["event_types"][e["event_type"]]+=1
    participant_first_seen={}
    for chain in relevant:
        e=event_by_id[chain["event_id"]]; month=_month(e["occurred_at"]); row=by_month[month]
        row["source_refs"].add(chain["confirming_source_ref"])
        for role in ROLES:
            pid=chain.get(role)
            if pid in people:
                row["participants"].add(pid)
                participant_first_seen[pid]=min(participant_first_seen.get(pid,e["occurred_at"]),e["occurred_at"])
    timeline=[]
    for month,row in sorted(by_month.items()):
        timeline.append({"month":month,"event_count":row["event_count"],"event_type_counts":dict(sorted(row["event_types"].items())),"unique_participant_count":len(row["participants"]),"participant_ids":sorted(row["participants"]),"source_refs":sorted(row["source_refs"])})
    all_participants=set(participant_first_seen)
    event_types=Counter(e["event_type"] for e in selected)
    unattributed=sorted({e["event_id"] for e in selected}-{c["event_id"] for c in relevant})
    active_months=[x["month"] for x in timeline if x["event_count"]]
    participant_rows=[{"person_id":pid,"first_seen_at":participant_first_seen[pid],"event_count":sum(pid in {c.get(k) for k in ROLES} for c in relevant)} for pid in sorted(all_participants)]
    return {"schema_version":"1.0","status":"REVIEW_REQUIRED" if unattributed else "PASS","customer_id":customer_id,"event_count":len(selected),"event_type_counts":dict(sorted(event_types.items())),"active_month_count":len(active_months),"first_activity_month":active_months[0] if active_months else None,"last_activity_month":active_months[-1] if active_months else None,"timeline":timeline,"participant_count":len(all_participants),"participants":participant_rows,"unattributed_event_ids":unattributed,"method":"occurred_at_monthly_event_and_participant_rollup_v1","limitations":["Activity volume and participant presence do not establish relationship quality, sentiment, or customer satisfaction.","Only supplied event subjects and attribution chains are analyzed; customer identity mapping must be validated upstream.","A missing attribution chain is a data-coverage gap, not evidence that no communication occurred."]}
