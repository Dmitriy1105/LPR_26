"""Task delegation ledger; no transfer of decision authority."""
from datetime import datetime
from budget_policy_v1 import load
from validate_organization_v1 import validate
def assign(instance,process,node,initiator,assigner,assignee,issued_at,due_at):
    org=load("organization_profile_v1.json")
    validate(org,load("budget_authority_v1.json"))
    people={p["id"]:p for p in org["people"]}
    roles={r["id"]:r for r in org["roles"]}
    if any(x not in people for x in (initiator,assigner,assignee)): raise ValueError("unknown participant")
    rules=[r for r in load("task_assignment_profile_v1.json")["rules"] if (r["process"],r["node"])==(process,node)]
    if len(rules)!=1: raise ValueError("missing or ambiguous assignment rule")
    rule=rules[0]
    if people[assigner]["role"] not in rule["assigner_roles"] or people[assignee]["role"] not in rule["assignee_roles"]: raise ValueError("assignment not authorized")
    current=people[assignee]["manager"]
    while current is not None and current!=assigner: current=people[current]["manager"]
    if current!=assigner: raise ValueError("outside management scope")
    if rule["capability"] and rule["capability"] not in roles[people[assignee]["role"]]["competencies"]: raise ValueError("missing competence")
    if datetime.fromisoformat(issued_at)>=datetime.fromisoformat(due_at): raise ValueError("invalid assignment period")
    return dict(assignment_id=instance+":"+node,instance_id=instance,process_id=process,node_id=node,initiator_id=initiator,delegator_id=assigner,assigned_actor_id=assignee,actual_actor_id=None,issued_at=issued_at,due_at=due_at,status="assigned",decision_authority_transferred=False)
def complete(assignment,actor,completed_at):
    if assignment["status"]!="assigned" or actor!=assignment["assigned_actor_id"]: raise ValueError("invalid completion actor or state")
    if not datetime.fromisoformat(assignment["issued_at"])<=datetime.fromisoformat(completed_at)<=datetime.fromisoformat(assignment["due_at"]): raise ValueError("completion outside assignment period")
    return {**assignment,"actual_actor_id":actor,"completed_at":completed_at,"status":"completed"}
