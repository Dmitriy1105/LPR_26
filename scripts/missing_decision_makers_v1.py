"""Evidence-based gap detection against an explicitly supplied expected decision-maker roster."""
from event_chronology_v1 import validate_events
from decision_attribution_chain_v1 import validate_attribution_chain
ROLES=("participant_id","utterance_author_id","action_executor_id","addressee_id")
def detect_missing_decision_makers(org,events,chains,expected_roster):
    validate_events(events)
    validate_attribution_chain(org,events,chains)
    if not isinstance(expected_roster,list): raise ValueError("expected_roster must be a list")
    people={p["id"]:p for p in org.get("people",[])}
    expected={}; seen=set()
    for item in expected_roster:
        if not isinstance(item,dict) or not isinstance(item.get("person_id"),str) or not item["person_id"].strip(): raise ValueError("invalid expected roster entry")
        pid=item["person_id"]
        if pid in seen: raise ValueError("duplicate expected person")
        seen.add(pid)
        if pid not in people: raise ValueError("expected person not present in organization registry")
        expected[pid]={"role":item.get("expected_role"),"required":bool(item.get("required",True))}
    observed=set()
    for chain in chains:
        for key in ROLES:
            pid=chain.get(key)
            if pid in people: observed.add(pid)
    missing=sorted(pid for pid,item in expected.items() if item["required"] and pid not in observed)
    optional_missing=sorted(pid for pid,item in expected.items() if not item["required"] and pid not in observed)
    observed_rows=[]
    for pid,item in sorted(expected.items()):
        observed_rows.append({"person_id":pid,"expected_role":item["role"],"required":item["required"],"observed":pid in observed,"status":"OBSERVED" if pid in observed else ("MISSING_REQUIRED" if item["required"] else "MISSING_OPTIONAL")})
    expected_roles={item["role"] for item in expected.values() if item["required"] and item["role"]}
    observed_roles={people[pid].get("role") for pid in observed}
    missing_roles=sorted(expected_roles-observed_roles)
    events_without_chain=sorted({e["event_id"] for e in events}-{c["event_id"] for c in chains})
    denominator=sum(1 for item in expected.values() if item["required"])
    covered=denominator-len(missing)
    return {"schema_version":"1.0","status":"REVIEW_REQUIRED" if missing or missing_roles or events_without_chain else "PASS","expected_required_count":denominator,"observed_required_count":covered,"coverage_ratio":round(covered/denominator,4) if denominator else 1.0,"missing_required_person_ids":missing,"missing_optional_person_ids":optional_missing,"missing_required_roles":missing_roles,"events_without_attribution":events_without_chain,"roster_results":observed_rows,"method":"explicit_roster_vs_attributed_communication_v1","limitations":["A person is considered observed if referenced in any attribution role; this does not prove decision authority.","Missing-person detection is only as complete as the explicitly supplied expected roster.","Role labels are descriptive metadata, not proof that a role-holder is a decision maker.","Synthetic organization members do not represent external customer contacts unless explicitly mapped."]}
