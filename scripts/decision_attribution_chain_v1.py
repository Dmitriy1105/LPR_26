"""Evidence-backed attribution chain for organizational decisions."""
from event_chronology_v1 import validate_events,chronology
FIELDS=("participant_id","utterance_author_id","action_executor_id","addressee_id","confirming_source_ref")
def validate_attribution_chain(org,events,chains):
    validate_events(events)
    people={p["id"] for p in org.get("people",[])}
    by_event={e["event_id"]:e for e in events}
    seen=set(); results=[]
    for c in chains:
        if not isinstance(c,dict): raise ValueError("chain must be an object")
        if not isinstance(c.get("chain_id"),str) or not c["chain_id"].strip() or c["chain_id"] in seen: raise ValueError("missing or duplicate chain id")
        seen.add(c["chain_id"])
        if c.get("event_id") not in by_event: raise ValueError("chain event missing")
        missing=[k for k in FIELDS if not isinstance(c.get(k),str) or not c[k].strip()]
        if missing:
            results.append({"chain_id":c["chain_id"],"event_id":c["event_id"],"status":"INCOMPLETE","missing_fields":missing}); continue
        unknown={k:c[k] for k in FIELDS[:-1] if c[k] not in people}
        if unknown: raise ValueError("unknown person reference")
        event=by_event[c["event_id"]]
        if c["action_executor_id"]!=event["actor_id"]: raise ValueError("executor differs from event actor")
        if c["confirming_source_ref"]!=event["source_ref"]: raise ValueError("confirming source differs from event source")
        results.append({"chain_id":c["chain_id"],"event_id":c["event_id"],"status":"COMPLETE","missing_fields":[]})
    incomplete=[r["chain_id"] for r in results if r["status"]!="COMPLETE"]
    return {"schema_version":"1.0","status":"PASS" if not incomplete else "REVIEW_REQUIRED","chain_count":len(results),"complete_count":len(results)-len(incomplete),"incomplete_chain_ids":incomplete,"results":results,"chronology":[e["event_id"] for e in chronology(events)]}
