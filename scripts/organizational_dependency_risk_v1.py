"""Heuristic concentration and single-person dependency indicators from attributed evidence."""
from collections import Counter
from event_chronology_v1 import validate_events
from decision_attribution_chain_v1 import validate_attribution_chain
ATTRIBUTION_ROLES=("participant_id","utterance_author_id","action_executor_id","addressee_id")
def assess_dependency_risk(org,events,chains,high_share_threshold=0.50,medium_share_threshold=0.35):
    validate_events(events)
    if not 0 < medium_share_threshold < high_share_threshold <= 1: raise ValueError("invalid concentration thresholds")
    validate_attribution_chain(org,events,chains)
    people={p["id"] for p in org.get("people",[])}
    counts=Counter(); event_people={}
    for chain in chains:
        if chain.get("event_id") not in {e["event_id"] for e in events}: raise ValueError("unknown event")
        present={chain[k] for k in ATTRIBUTION_ROLES if isinstance(chain.get(k),str) and chain[k] in people}
        for person in present: counts[person]+=1
        event_people[chain["event_id"]]=event_people.get(chain["event_id"],set())|present
    total=sum(counts.values())
    shares={p:(counts[p]/total if total else 0.0) for p in people}
    ranked=sorted(({"person_id":p,"attributed_event_count":counts[p],"share":round(shares[p],4)} for p in people),key=lambda x:(-x["share"],x["person_id"]))
    top=ranked[0] if ranked else None
    hhi=round(sum(v*v for v in shares.values()),4)
    top_share=top["share"] if top else 0.0
    risk="HIGH" if top_share>=high_share_threshold else ("MEDIUM" if top_share>=medium_share_threshold else "LOW")
    total_events=len(events); top_id=top["person_id"] if top else None
    events_remaining=sum(1 for eid,present in event_people.items() if top_id not in present) if top_id else len(event_people)
    coverage_after_removal=round(events_remaining/total_events,4) if total_events else 1.0
    missing=[e["event_id"] for e in events if e["event_id"] not in event_people]
    return {"schema_version":"1.0","status":"PASS" if not missing else "REVIEW_REQUIRED","event_count":total_events,"attributed_event_count":len(event_people),"unattributed_event_ids":missing,"top_person":top,"top_person_concentration":round(top_share,4),"hhi_concentration":hhi,"heuristic_risk_level":risk,"event_coverage_after_top_person_removal":coverage_after_removal,"people_ranked":ranked[:10],"method":"attribution_role_event_counts_v1","calibrated_risk_probability":False,"limitations":["Concentration is a proxy for dependency, not proof of business criticality or actual influence.","Thresholds are configurable heuristics and require validation against real customer outcomes.","Synthetic organization members are not equivalent to external customer decision makers."]}
