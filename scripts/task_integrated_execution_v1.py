"""Explicit task-integrated simulation profile; no transfer of approval authority."""
from datetime import datetime,timedelta
from hashlib import sha256
from budget_policy_v1 import ROOT,load
from authority_execution_v1 import execute_authoritative
from task_assignment_v1 import assign,complete
def execute_with_tasks(pid,inputs,plan,instance="I1"):
    rules=load("task_assignment_profile_v1.json")["rules"]
    keys={(r["process"],r["node"]) for r in rules}
    if len(keys)!=len(rules): raise ValueError("duplicate task rule")
    used=set()
    def handler(process,node,path,context,step):
        if (process,node) not in keys: return []
        key=path+":"+node+":"+str(step)
        if key not in plan: raise ValueError("missing task plan "+key)
        entry=plan[key]
        if set(entry)!={"assigner","assignee","issued_at","due_at","completed_at"}: raise ValueError("invalid task plan fields")
        if key in used: raise ValueError("duplicate task visit")
        used.add(key)
        record=assign(path,process,node,context["initiator"],entry["assigner"],entry["assignee"],entry["issued_at"],entry["due_at"])
        record["assignment_id"]=key
        done=complete(record,entry["assignee"],entry["completed_at"])
        return [dict(event="task_assigned",assignment=record),dict(event="task_completed",assignment=done)]
    result=execute_authoritative(pid,inputs,instance,task_handler=handler)
    if used!=set(plan): raise ValueError("unused task plan")
    result["task_profile_sha256"]=sha256((ROOT/"models/organization/task_assignment_profile_v1.json").read_bytes()).hexdigest()
    result["execution_mode"]="authoritative_task_simulation"
    return result
