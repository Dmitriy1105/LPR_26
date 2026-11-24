"""Explainable evidence-based decision-maker role classification; requires human review."""
from multifactor_decision_maker_v1 import rank_decision_makers
def classify_decision_maker_roles(org,events,chains,grants=None,delegations=None,decisions=None,weights=None):
    ranked=rank_decision_makers(org,events,chains,grants,delegations,decisions,weights)
    decision_rows=decisions or []
    actor_counts={}
    approval_counts={}
    for d in decision_rows:
        actor=d.get("actor_id")
        if actor:
            actor_counts[actor]=actor_counts.get(actor,0)+1
            if d.get("permission") in ("approve","approval","final_approval"):
                approval_counts[actor]=approval_counts.get(actor,0)+1
    classifications=[]
    for row in ranked["ranked_candidates"]:
        pid=row["person_id"]; score=row["score"]; factors=row["factors"]
        authorized=row["authorized_decision_count"]
        if authorized>0:
            role="AUTHORIZED_DECISION_MAKER"; basis=["validated_direct_or_delegated_authority"]
        elif approval_counts.get(pid,0)>0:
            role="APPROVAL_PARTICIPANT"; basis=["recorded_approval_action_without_confirmed_authority"]
        elif factors["influence"]>=0.5 and factors["participation"]>=0.25:
            role="EVIDENCE_LINKED_INFLUENCER"; basis=["repeated_attributed_interaction","evidence_linked_graph_position"]
        elif factors["execution"]>=0.5:
            role="DECISION_EXECUTOR"; basis=["repeated_attributed_action_execution"]
        elif factors["participation"]>=0.25:
            role="ACTIVE_STAKEHOLDER"; basis=["repeated_attributed_participation"]
        elif factors["formal_role"]>0:
            role="FORMAL_ROLE_CANDIDATE"; basis=["formal_position_only"]
        else:
            role="INSUFFICIENT_EVIDENCE"; basis=["insufficient_observed_decision_evidence"]
        classifications.append({"person_id":pid,"role_class":role,"multifactor_score":score,"authorized_decision_count":authorized,"recorded_decision_count":actor_counts.get(pid,0),"classification_basis":basis,"human_review_required":True})
    return {"schema_version":"1.0","status":"REVIEW_REQUIRED" if ranked["status"]!="PASS" or classifications else "EMPTY","classification_count":len(classifications),"classifications":classifications,"authority_status":ranked["authority_status"],"method":"rule_based_evidence_role_classification_v1","limitations":["Only decisions and authority records supplied to this function can support an authorized decision-maker classification.","Approval action text without verified authority is not treated as proof of approval power.","Influence, participation and execution are evidence indicators, not formal authority.","All classifications require human review; this module does not make legal or organizational determinations."]}
