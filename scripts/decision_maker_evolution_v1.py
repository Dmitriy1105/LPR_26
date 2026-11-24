"""Descriptive month-over-month participant trend signals; not a statistical or causal forecast."""
from collections import defaultdict
from datetime import datetime,timezone
from event_chronology_v1 import validate_events,chronology
from decision_attribution_chain_v1 import validate_attribution_chain
ROLE_FIELDS=("participant_id","utterance_author_id","action_executor_id","addressee_id")
def _month(value):
    return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc).strftime("%Y-%m")
def analyze_decision_maker_evolution(org,events,chains,customer_id=None):
    validate_events(events); validate_attribution_chain(org,events,chains)
    people={p["id"]:p for p in org.get("people",[])}
    selected=chronology([e for e in events if customer_id is None or e["subject_id"]==customer_id])
    selected_ids={e["event_id"] for e in selected}
    relevant=[c for c in chains if c["event_id"] in selected_ids]
    event_map={e["event_id"]:e for e in selected}
    monthly=defaultdict(lambda:defaultdict(set)); refs=defaultdict(lambda:defaultdict(set))
    for chain in relevant:
        event=event_map[chain["event_id"]]; month=_month(event["occurred_at"])
        for field in ROLE_FIELDS:
            pid=chain.get(field)
            if pid in people:
                monthly[pid][month].add(event["event_id"])
                refs[pid][month].add(chain["confirming_source_ref"])
    months=sorted({_month(e["occurred_at"]) for e in selected})
    latest=months[-1] if months else None
    previous=months[-2] if len(months)>1 else None
    rows=[]
    for pid,person in sorted(people.items()):
        history=monthly.get(pid,{})
        current=len(history.get(latest,set())) if latest else 0
        prior=len(history.get(previous,set())) if previous else 0
        observed_months=sorted(history)
        if latest is None or len(months)<2 or not observed_months:
            trend="INSUFFICIENT_HISTORY"; signal="INSUFFICIENT_EVIDENCE"; predicted="UNKNOWN"
        elif current>prior:
            trend="INCREASING"; signal="EMERGING_PARTICIPATION" if prior==0 else "INCREASING_ACTIVITY"; predicted="POSSIBLE_INCREASE"
        elif current<prior:
            trend="DECREASING"; signal="POTENTIAL_ACTIVITY_DECLINE" if current>0 else "POTENTIAL_DISENGAGEMENT"; predicted="POSSIBLE_DECREASE"
        else:
            trend="STABLE"; signal="STABLE_ACTIVITY"; predicted="NO_CLEAR_CHANGE"
        rows.append({"person_id":pid,"role":person.get("role"),"trend":trend,"signal":signal,"previous_month":previous,"previous_event_count":prior,"latest_month":latest,"latest_event_count":current,"observed_active_months":observed_months,"latest_source_refs":sorted(refs.get(pid,{}).get(latest,set())) if latest else [],"next_period_signal":predicted,"human_review_required":True})
    unattributed=sorted(selected_ids-{c["event_id"] for c in relevant})
    return {"schema_version":"1.0","status":"REVIEW_REQUIRED" if unattributed or len(months)<2 else "PASS","customer_id":customer_id,"method":"two_latest_observed_months_directional_heuristic_v1","observation_months":months,"previous_month":previous,"latest_month":latest,"person_count":len(rows),"signals":rows,"unattributed_event_ids":unattributed,"limitations":["This is a descriptive two-month directional heuristic, not a trained predictive model or statistically validated forecast.","Two adjacent observed months may be sparse or seasonal; no confidence interval or calibrated probability is produced.","A decline in recorded activity does not prove a relationship is weakening or a person has left the decision process.","No customer-side identity, job-change, sentiment, or future event is inferred.","All signals require human review and should be validated against subsequent observations."]}
