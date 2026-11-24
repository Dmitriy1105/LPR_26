"""Explainable candidate ranking for decision-maker review; not an autonomous authority determination."""
from collections import Counter
from event_chronology_v1 import validate_events
from decision_attribution_chain_v1 import validate_attribution_chain
from organizational_influence_v1 import build_influence_graph
from decision_authority_reconciliation_v1 import reconcile_decisions
def rank_decision_makers(org,events,chains,grants=None,delegations=None,decisions=None,weights=None):
    validate_events(events); validate_attribution_chain(org,events,chains)
    weights=weights or {"formal_role":0.20,"authority":0.25,"participation":0.20,"execution":0.15,"influence":0.10,"evidence_coverage":0.10}
    if set(weights)!={"formal_role","authority","participation","execution","influence","evidence_coverage"}: raise ValueError("weights must define all six factors")
    if any(not isinstance(v,(int,float)) or v<0 for v in weights.values()) or sum(weights.values())<=0: raise ValueError("invalid factor weights")
    total=sum(weights.values()); weights={k:v/total for k,v in weights.items()}
    people={p["id"]:p for p in org.get("people",[])}
    units={u["id"]:u for u in org.get("units",[])}
    role_counts=Counter(); participation=Counter(); execution=Counter(); evidence=Counter()
    for c in chains:
        for key in ("participant_id","utterance_author_id","action_executor_id","addressee_id"):
            if c.get(key) in people: participation[c[key]]+=1
        if c.get("action_executor_id") in people: execution[c["action_executor_id"]]+=1
        if c.get("confirming_source_ref"): evidence[c["action_executor_id"]]+=1
    for d in decisions or []:
        if d.get("actor_id") in people: role_counts[d["actor_id"]]+=1
    influence=build_influence_graph(org,events,chains)
    influence_scores={x["person_id"]:x["weighted_influence_score"] for x in influence["nodes"]}
    authority_scores=Counter()
    authority_status="NOT_ASSESSED"
    if decisions:
        result=reconcile_decisions(org,grants or [],delegations or [],events,decisions)
        authority_status=result["status"]
        for row in result["results"]:
            if row["authorized"]: authority_scores[row["actor_id"]]+=1
    max_values={
      "formal_role":max((1 if p["role"] in ("director","head_of_sales","finance_manager","technical_manager","procurement_manager","legal_manager","project_office_manager","security_manager","information_security_manager") else 0 for p in people.values()),default=0),
      "authority":max(authority_scores.values(),default=0),"participation":max(participation.values(),default=0),
      "execution":max(execution.values(),default=0),"influence":max(influence_scores.values(),default=0),"evidence_coverage":max(evidence.values(),default=0)}
    rows=[]
    for pid,p in sorted(people.items()):
        unit=units.get(p.get("unit"),{})
        factors={
          "formal_role":1.0 if p["role"] in ("director","head_of_sales","finance_manager","technical_manager","procurement_manager","legal_manager","project_office_manager","security_manager","information_security_manager") else 0.0,
          "authority":authority_scores[pid]/max_values["authority"] if max_values["authority"] else 0.0,
          "participation":participation[pid]/max_values["participation"] if max_values["participation"] else 0.0,
          "execution":execution[pid]/max_values["execution"] if max_values["execution"] else 0.0,
          "influence":influence_scores.get(pid,0)/max_values["influence"] if max_values["influence"] else 0.0,
          "evidence_coverage":evidence[pid]/max_values["evidence_coverage"] if max_values["evidence_coverage"] else 0.0}
        score=round(sum(weights[k]*factors[k] for k in weights)*100,2)
        rows.append({"person_id":pid,"role":p["role"],"department":unit.get("department"),"score":score,"factors":{k:round(v,4) for k,v in factors.items()},"authorized_decision_count":authority_scores[pid],"participation_count":participation[pid],"execution_count":execution[pid],"evidence_count":evidence[pid],"review_required":not decisions or authority_status!="PASS"})
    rows.sort(key=lambda x:(-x["score"],x["person_id"]))
    return {"schema_version":"1.0","status":"REVIEW_REQUIRED" if not decisions or authority_status!="PASS" else "PASS","method":"weighted_normalized_evidence_ranking_v1","weights":weights,"candidate_count":len(rows),"ranked_candidates":rows,"authority_status":authority_status,"limitations":["Ranking is a review aid, not a finding that a person is the legal or actual decision maker.","Formal role points use a transparent role allowlist and do not prove delegated authority.","Counts are normalized within this input batch and are not comparable across datasets without calibration.","No customer-side contact data is inferred from internal organization records.","Missing decisions or evidence leave authority status NOT_ASSESSED and require human review."]}
