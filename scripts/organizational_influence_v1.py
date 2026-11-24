"""Evidence-derived organizational interaction graph; formal hierarchy is not treated as influence."""
from collections import defaultdict
from event_chronology_v1 import validate_events,chronology
from decision_attribution_chain_v1 import validate_attribution_chain
def build_influence_graph(org,events,chains):
    validate_events(events)
    attr=validate_attribution_chain(org,events,chains)
    people={p["id"] for p in org.get("people",[])}
    links=defaultdict(lambda:{"weight":0,"event_ids":[],"evidence_refs":[],"relation_types":set()})
    for chain in chains:
        if any(not chain.get(k) for k in ("participant_id","utterance_author_id","action_executor_id","addressee_id","confirming_source_ref")): continue
        event=next(e for e in events if e["event_id"]==chain["event_id"])
        relations=(("participant_id","utterance_author_id","authored_utterance"),("utterance_author_id","action_executor_id","action_following_utterance"),("action_executor_id","addressee_id","action_addressed_to"))
        for src_key,dst_key,kind in relations:
            src,dst=chain[src_key],chain[dst_key]
            if src not in people or dst not in people: raise ValueError("unknown person in influence edge")
            if src==dst: continue
            item=links[(src,dst)]; item["weight"]+=1; item["event_ids"].append(event["event_id"]); item["evidence_refs"].append(chain["confirming_source_ref"]); item["relation_types"].add(kind)
    nodes=[]
    for person in sorted(people):
        nodes.append({"person_id":person,"in_degree":0,"out_degree":0,"weighted_influence_score":0})
    index={n["person_id"]:n for n in nodes}
    edges=[]
    for (src,dst),item in sorted(links.items()):
        weight=item["weight"]; index[src]["out_degree"]+=1; index[dst]["in_degree"]+=1; index[dst]["weighted_influence_score"]+=weight
        edges.append({"source":src,"target":dst,"weight":weight,"event_ids":sorted(set(item["event_ids"])),"evidence_refs":sorted(set(item["evidence_refs"])),"relation_types":sorted(item["relation_types"])})
    ranked=sorted(nodes,key=lambda n:(-n["weighted_influence_score"],n["person_id"]))
    return {"schema_version":"1.0","status":"PASS" if attr["status"]=="PASS" else "REVIEW_REQUIRED","node_count":len(nodes),"edge_count":len(edges),"nodes":nodes,"edges":edges,"top_evidence_linked_influence":ranked[:10],"limitations":["Edges represent observed communication/action attribution, not proof of persuasion, authority, or causal influence.","Formal reporting hierarchy is deliberately not counted as influence.","Scores are evidence counts, not calibrated influence estimates."]}
def detect_missing_participants(org,events,chains,expected_participant_ids=None):
    people={p["id"] for p in org.get("people",[])}
    event_ids={e["event_id"] for e in events}
    chain_events={c.get("event_id") for c in chains}
    unknown=sorted({c.get("participant_id") for c in chains if c.get("participant_id") not in people})
    missing=sorted(event_ids-chain_events)
    expected=set(expected_participant_ids or people)
    observed={c.get("participant_id") for c in chains if c.get("participant_id") in people}
    return {"status":"PASS" if not missing and not unknown else "REVIEW_REQUIRED","events_without_attribution":missing,"unknown_participants":unknown,"expected_people_without_observed_participation":sorted(expected-observed),"coverage_ratio":round(len(observed & expected)/len(expected),4) if expected else 1.0}
def main():
    import json
    from organization_engine_v1 import generate
    org=generate(seed=42,count=1)[0]
    print(json.dumps(build_influence_graph(org,[],[]),ensure_ascii=False,sort_keys=True))
if __name__=="__main__": main()
