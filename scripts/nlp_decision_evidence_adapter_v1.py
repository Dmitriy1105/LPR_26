"""Conservative bridge from NLP v3.3 evidence to the organization engine.
Never converts participant membership or role co-occurrence into verified authorship or authority.
"""
from collections import Counter
REQUIRED=("signal_id","activity_id","segment_id","signal_type","signal_text","evidence_ref")
def adapt_nlp_evidence(signals,ground_truth=None,activity_participants=None):
    if not isinstance(signals,list): raise ValueError("signals must be a list")
    truth={}; 
    for row in ground_truth or []:
        if not isinstance(row,dict) or not row.get("activity_id"): raise ValueError("invalid ground truth row")
        key=(str(row["activity_id"]),row.get("action_segment_index"),row.get("synthetic_action_text"))
        if key in truth: raise ValueError("duplicate ground truth annotation")
        truth[key]=row
    participant_index={str(k):sorted({str(x) for x in v}) for k,v in (activity_participants or {}).items()}
    seen=set(); output=[]; counts=Counter()
    for row in signals:
        if not isinstance(row,dict) or any(not isinstance(row.get(k),str) or not row[k].strip() for k in REQUIRED):
            raise ValueError("signal missing required evidence field")
        sid=row["signal_id"]
        if sid in seen: raise ValueError("duplicate signal id")
        seen.add(sid)
        activity=row["activity_id"]
        annotation=truth.get((activity,row.get("segment_index"),row["signal_text"]))
        verified=bool(annotation and annotation.get("actor_identity_verified") is True and isinstance(annotation.get("actor_contact_id"),str) and annotation["actor_contact_id"].strip())
        candidates=participant_index.get(activity,[])
        record={"signal_id":sid,"activity_id":activity,"segment_id":row["segment_id"],"signal_type":row["signal_type"],"signal_text":row["signal_text"],"evidence_ref":row["evidence_ref"],"participant_candidate_ids":candidates,"actor_contact_id":annotation.get("actor_contact_id") if verified else None,"actor_identity_verified":verified,"attribution_status":"verified_ground_truth" if verified else ("participant_candidates_only" if candidates else "unattributed"),"role_context":row.get("role_context"),"role_context_is_person_attribution":False,"eligible_for_person_level_decision_chain":verified,"human_review_required":True}
        output.append(record); counts[record["attribution_status"]]+=1
    return {"schema_version":"1.0","status":"PASS" if output else "EMPTY","signal_count":len(output),"unique_signal_ids":len(seen),"attribution_counts":dict(sorted(counts.items())),"signals":output,"limitations":["NLP signal detection is not proof of a person's authorship, statement subject, or decision authority.","CRM participants are candidate context only; they are not assigned as signal actors.","Role mentions and same-segment co-occurrence remain context, not person attribution.","Only an explicit, independently verified ground-truth actor_contact_id can be eligible for person-level linkage.","This adapter does not create decision events or authority grants."]}
