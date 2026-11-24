"""Explainable evidence-coverage confidence and review-risk indicators (not calibrated probabilities)."""
from decision_attribution_chain_v1 import validate_attribution_chain
from decision_evidence_provenance_v1 import audit_evidence_provenance
from event_chronology_v1 import validate_events
def assess_decision_confidence(org,events,chains,evidence_records,decisions):
    validate_events(events)
    if not isinstance(decisions,list): raise ValueError("decisions must be a list")
    if not decisions: return {"schema_version":"1.0","status":"EMPTY","decision_count":0,"results":[],"method":"rule_based_evidence_coverage_v1","probability_calibrated":False}
    attr=validate_attribution_chain(org,events,chains)
    provenance=audit_evidence_provenance(events,evidence_records)
    event_by_id={e["event_id"]:e for e in events}
    chain_by_event={r["event_id"]:r for r in attr["results"]}
    provenance_refs={r["source_ref"] for r in evidence_records}
    rows=[]
    for d in decisions:
        if any(k not in d for k in ("decision_id","source_event_id","actor_id")): raise ValueError("missing decision identity fields")
        event=event_by_id.get(d["source_event_id"])
        if event is None: raise ValueError("decision source event missing")
        reasons=[]; score=100
        chain=chain_by_event.get(event["event_id"])
        if chain is None or chain["status"]!="COMPLETE": score-=30; reasons.append("attribution_chain_incomplete")
        if event["source_ref"] not in provenance_refs: score-=30; reasons.append("evidence_provenance_missing")
        if event["actor_id"]!=d["actor_id"]: score-=40; reasons.append("actor_mismatch")
        if event["event_type"] not in ("decision","approval"): score-=20; reasons.append("event_not_decision_or_approval")
        score=max(0,score)
        risk="LOW" if score>=80 else ("MEDIUM" if score>=50 else "HIGH")
        rows.append({"decision_id":d["decision_id"],"source_event_id":event["event_id"],"evidence_coverage_score":score,"risk_level":risk,"review_required":score<80,"risk_reasons":reasons})
    return {"schema_version":"1.0","status":"PASS" if all(x["evidence_coverage_score"]>=80 for x in rows) else "REVIEW_REQUIRED","decision_count":len(rows),"low_risk_count":sum(x["risk_level"]=="LOW" for x in rows),"medium_risk_count":sum(x["risk_level"]=="MEDIUM" for x in rows),"high_risk_count":sum(x["risk_level"]=="HIGH" for x in rows),"results":rows,"method":"rule_based_evidence_coverage_v1","probability_calibrated":False,"provenance_status":provenance["status"],"attribution_status":attr["status"],"limitations":["Score is a deterministic evidence-coverage heuristic, not a statistical confidence or probability.","SHA-256 format validation does not authenticate the source document.","No source reliability ranking or human adjudication is inferred."]}
