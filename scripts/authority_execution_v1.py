"""Authoritative simulation entry point; trusted repository configuration only."""
import json
from hashlib import sha256
from budget_policy_v1 import ROOT,load,prepare
from universal_bpmn_engine import execute
PROTECTED={"authorized","competent","withinLimit","budgetAuthorized","dealAuthorized","dealRequirementsMet"}
def role_policy(c,kind):
    org=load("organization_profile_v1.json")
    people={p["id"]:p for p in org["people"]}
    if c["actor"] not in people or c["initiator"] not in people: raise ValueError("unknown person")
    role=next(r for r in org["roles"] if r["id"]==people[c["actor"]]["role"])
    key="competent" if kind=="technical" else "authorized"
    capability="technical.assess" if kind=="technical" else "deal.approve"
    return {key:capability in role["competencies" if kind=="technical" else "grants"],"authority_role":role["id"],"authority_capability":capability}
def technical(c): return role_policy(c,"technical")
def deal(c): return role_policy(c,"deal")
def execute_authoritative(pid,inputs,instance="I1"):
    allowed={
      "technical_expertise":{"actor","initiator","requirementsMet","remediable"},
      "deal_approval":{"actor","initiator","requirementsMet","revisionAllowed"},
      "budget_approval":{"actor","initiator","amount","as_of","fundsAvailable"},
      "budget_escalation_universal":{"actor","initiator","amount","as_of","fundsAvailable"},
      "corporate_multilevel_universal":{"technicalActor","budgetActor","dealActor","initiator","amount","as_of","fundsAvailable","technicalRequirementsMet","remediable"}}
    if pid not in allowed or set(inputs)!=allowed[pid]: raise ValueError("invalid authoritative inputs")
    org=load("organization_profile_v1.json")
    people={p["id"] for p in org["people"]}
    if any(v not in people for k,v in inputs.items() if k=="actor" or k=="initiator" or k.endswith("Actor")): raise ValueError("unknown person")
    registry=json.loads((ROOT/"models/process_registry_universal_v1.json").read_text())
    registry["processes"]=[s for s in registry["processes"] if s["id"] in allowed]
    specs={s["id"]:s for s in registry["processes"]}
    for p,node,op in [("technical_expertise","assess","technical_authority"),("deal_approval","decide","deal_authority"),("budget_approval","decide","budget_authority")]:
        specs[p].setdefault("before",{})[node]=[op]
    c=specs["corporate_multilevel_universal"]["calls"]
    for name,actor,key in [("technical","technicalActor","competent"),("deal","dealActor","authorized")]:
        c[name]["inputs"].pop(key)
        c[name]["inputs"].update(actor={"ref":actor},initiator={"ref":"initiator"})
    a=specs["budget_escalation_universal"]["calls"]["assess"]["inputs"]
    for key in ("authorized","withinLimit"): a.pop(key)
    for key in ("amount","as_of","initiator"): a[key]={"ref":key}
    result=execute(pid,inputs,registry,instance=instance,policy_operations={"technical_authority":technical,"deal_authority":deal})
    result["execution_mode"]="authoritative_simulation"
    result["authority_sources"]={name:sha256((ROOT/"models/organization"/name).read_bytes()).hexdigest() for name in ("organization_profile_v1.json","budget_authority_v1.json")}
    return result
