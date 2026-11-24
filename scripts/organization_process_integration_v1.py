"""Integration boundary connecting BPMN task intent, DMN decision inputs and organization evidence."""
from event_chronology_v1 import validate_events,chronology
from temporal_authority_v1 import authorize_at
from delegation_authority_v1 import authorize_delegated_at
def evaluate_task(org,task,grants,delegations,events,as_of,amount=None):
    required=("task_id","action","required_permission","actor_id","subject_id","bpmn_process_id","bpmn_task_id","dmn_decision_id")
    if any(k not in task for k in required): raise ValueError("missing BPMN/DMN task binding")
    for k in ("task_id","action","actor_id","subject_id","bpmn_process_id","bpmn_task_id","dmn_decision_id"):
        if not isinstance(task[k],str) or not task[k].strip(): raise ValueError("empty task binding: "+k)
    if task["required_permission"] not in ("approve","final_decision"): raise ValueError("invalid required permission")
    validate_events(events)
    direct=authorize_at(org,grants,task["actor_id"],task["action"],task["required_permission"],as_of,amount)
    delegated=authorize_delegated_at(org,grants,delegations,task["actor_id"],task["action"],task["required_permission"],as_of,amount)
    matched=[e for e in chronology(events) if e.get("actor_id")==task["actor_id"] and e.get("subject_id")==task["subject_id"]]
    authority=direct if direct["authorized"] else delegated
    return dict(task_id=task["task_id"],bpmn_process_id=task["bpmn_process_id"],bpmn_task_id=task["bpmn_task_id"],dmn_decision_id=task["dmn_decision_id"],actor_id=task["actor_id"],subject_id=task["subject_id"],action=task["action"],permission=task["required_permission"],as_of=as_of,authorized=authority["authorized"],authority_source="direct" if direct["authorized"] else ("delegated" if delegated["authorized"] else None),authority_result=authority,event_evidence_count=len(matched),event_ids=[e["event_id"] for e in matched],decision="ALLOW" if authority["authorized"] else "DENY")
def build_decision_trace(task_result,dmn_result,event_ids):
    if task_result["decision"] not in ("ALLOW","DENY"): raise ValueError("invalid authorization decision")
    if not isinstance(dmn_result,dict) or "decision_id" not in dmn_result or "outcome" not in dmn_result: raise ValueError("invalid DMN result")
    if not isinstance(event_ids,list) or any(not isinstance(x,str) or not x for x in event_ids): raise ValueError("invalid trace event ids")
    return dict(trace_version="1.0",task=task_result,dmn=dict(decision_id=dmn_result["decision_id"],outcome=dmn_result["outcome"]),event_ids=list(dict.fromkeys(event_ids)),integrity_status="evidence_linked")
