"""Evidence-linked cross-department interaction analysis; counts are not causal influence."""
from collections import defaultdict
from decision_attribution_chain_v1 import validate_attribution_chain
from event_chronology_v1 import validate_events
def analyze_interdepartmental_influence(org,events,chains):
    validate_events(events); attr=validate_attribution_chain(org,events,chains)
    people={p["id"]:p for p in org.get("people",[])}
    units={u["id"]:u for u in org.get("units",[])}
    department_by_person={}
    for pid,p in people.items():
        unit=units.get(p.get("unit"))
        if unit is None: raise ValueError("person references unknown unit")
        department_by_person[pid]=unit.get("department")
    departments=sorted({d for d in department_by_person.values() if d and d!="headquarters"})
    counts=defaultdict(lambda:{"interaction_count":0,"event_ids":set(),"source_refs":set(),"person_pairs":set()})
    person_pairs=defaultdict(set); observed=set(); event_departments=defaultdict(set)
    for chain in chains:
        ids=[chain.get(k) for k in ("participant_id","utterance_author_id","action_executor_id","addressee_id")]
        valid=[pid for pid in ids if pid in people]
        observed.update(valid)
        event=next(e for e in events if e["event_id"]==chain["event_id"])
        for pid in valid: event_departments[event["event_id"]].add(department_by_person[pid])
        for i,src in enumerate(valid):
            for dst in valid[i+1:]:
                sd,dd=department_by_person[src],department_by_person[dst]
                if not sd or not dd or sd==dd: continue
                key=tuple(sorted((sd,dd)))
                row=counts[key]; row["interaction_count"]+=1; row["event_ids"].add(event["event_id"]); row["source_refs"].add(chain["confirming_source_ref"]); row["person_pairs"].add(tuple(sorted((src,dst))))
                person_pairs[key].add((src,dst))
    matrix=[]
    for (a,b),row in sorted(counts.items()):
        matrix.append({"department_a":a,"department_b":b,"interaction_count":row["interaction_count"],"unique_event_count":len(row["event_ids"]),"unique_person_pair_count":len(row["person_pairs"]),"event_ids":sorted(row["event_ids"]),"source_refs":sorted(row["source_refs"])})
    active=sorted({d for ds in event_departments.values() for d in ds})
    isolated=sorted(set(departments)-set(active))
    missing_events=sorted({e["event_id"] for e in events}-{c["event_id"] for c in chains})
    return {"schema_version":"1.0","status":"REVIEW_REQUIRED" if attr["status"]!="PASS" or missing_events else "PASS","department_count":len(departments),"departments":departments,"cross_department_pair_count":len(matrix),"cross_department_interaction_count":sum(x["interaction_count"] for x in matrix),"interaction_matrix":matrix,"departments_observed":active,"departments_without_observed_interaction":isolated,"unattributed_event_ids":missing_events,"observed_person_count":len(observed),"method":"co_attributed_person_pairs_by_department_v1","limitations":["Interactions indicate co-attribution within a recorded event, not persuasion, authority, or causal influence.","Only departments represented in the supplied organization registry can be analyzed.","A missing department interaction may reflect incomplete CRM capture, not a true organizational silo.","Counts are not normalized for department size or communication opportunity."]}
