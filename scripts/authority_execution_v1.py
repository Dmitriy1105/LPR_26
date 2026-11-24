from registry_consolidation import compose
"""Authoritative simulation entry point using trusted declarative configuration."""
import json
from hashlib import sha256
from budget_policy_v1 import ROOT,load
from universal_bpmn_engine import execute
from validate_organization_v1 import validate
PROFILE="authority_execution_profile_v1.json"
def role_policy(c,policy):
    org=load("organization_profile_v1.json")
    people={p["id"]:p for p in org["people"]}
    if c["actor"] not in people or c["initiator"] not in people: raise ValueError("unknown person")
    role=next(r for r in org["roles"] if r["id"]==people[c["actor"]]["role"])
    capability=policy["capability"]
    return {policy["output"]:capability in role[policy["field"]],"authority_role":role["id"],"authority_capability":capability}
def execute_authoritative(pid,inputs,instance="I1",task_handler=None):
    validate(load("organization_profile_v1.json"),load("budget_authority_v1.json"))
    profile=load(PROFILE)
    allowed=profile["allowed_inputs"]
    if pid not in allowed or set(inputs)!=set(allowed[pid]): raise ValueError("invalid authoritative inputs")
    org=load("organization_profile_v1.json")
    people={p["id"] for p in org["people"]}
    if any(v not in people for k,v in inputs.items() if k=="actor" or k=="initiator" or k.endswith("Actor")): raise ValueError("unknown person")
    operations={name:(lambda c,p=policy:role_policy(c,p)) for name,policy in profile["role_policies"].items()}
    result=execute(pid,inputs,compose(profile),instance=instance,policy_operations=operations,task_handler=task_handler)
    result["execution_mode"]="authoritative_simulation"
    result["authority_sources"]={name:sha256((ROOT/"models/organization"/name).read_bytes()).hexdigest() for name in ("organization_profile_v1.json","budget_authority_v1.json",PROFILE)}
    return result
