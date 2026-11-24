"""Project explicit actor evidence without inferring human decision enactment."""
import json
from datetime import datetime
from task_integrated_execution_v1 import execute_with_tasks
def project(record):
    pending={}; completed=set(); rows=[]; active={}; last={}; previous=None
    for i,e in enumerate(record["events"]):
        path=e["instance_path"]; eid=e["event_id"]; kind=e["event"]
        if e["global_step"]!=i or e["previous_event_id"]!=previous or e["previous_local_event_id"]!=last.get(path): raise ValueError("trace chain")
        if eid in {r["source_event_id"] for r in rows}: raise ValueError("duplicate event")
        previous=eid; last[path]=eid
        if kind=="process_start": active[path]=e["process_id"]
        if path not in active: raise ValueError("inactive process")
        row=dict(source_event_id=eid,instance_path=path,process_id=active[path],node_id=e.get("node_id"),event=kind,initiator_id=None,delegator_id=None,assigned_actor_id=None,actual_actor_id=None,decision_subject_id=None,decision_actor_id=None,assignment_id=None)
        if kind in ("task_assigned","task_completed"):
            a=e["assignment"]; key=a["assignment_id"]
            if (a["instance_id"],a["process_id"],a["node_id"])!=(path,active[path],e["node_id"]): raise ValueError("assignment linkage")
            if a["decision_authority_transferred"] is not False: raise ValueError("authority transfer")
            if kind=="task_assigned":
                if key in pending or key in completed or a["status"]!="assigned" or a["actual_actor_id"] is not None: raise ValueError("assignment state")
                pending[key]=a
            else:
                old=pending.pop(key,None)
                if old is None or a["status"]!="completed" or a["actual_actor_id"]!=a["assigned_actor_id"]: raise ValueError("completion state")
                if any(a[k]!=v for k,v in old.items() if k not in ("status","actual_actor_id")): raise ValueError("assignment mutation")
                if not datetime.fromisoformat(a["issued_at"])<=datetime.fromisoformat(a["completed_at"])<=datetime.fromisoformat(a["due_at"]): raise ValueError("completion chronology")
                completed.add(key)
            for k in ("initiator_id","delegator_id","assigned_actor_id","actual_actor_id","assignment_id"): row[k]=a[k]
        if kind=="decision": row["decision_subject_id"]=e.get("actor_id")
        if kind=="process_end":
            if any(a["instance_id"]==path for a in pending.values()): raise ValueError("unfinished assignment")
            del active[path]
        rows.append(row)
    if pending or active: raise ValueError("incomplete trace")
    return rows
def replay(record,pid,inputs,plan,instance="I1"):
    expected=execute_with_tasks(pid,inputs,plan,instance)
    if json.dumps(record,sort_keys=True)!=json.dumps(expected,sort_keys=True): raise ValueError("task replay mismatch")
    return dict(status="PASS",rows=len(project(record)))
