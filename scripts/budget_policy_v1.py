"""Organization policy adapters; routing remains in BPMN."""
import json
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT/"models/organization"/name).read_text())
def prepare(c):
    org=load("organization_profile_v1.json")
    people={p["id"]:p for p in org["people"]}
    roles={r["id"]:r for r in org["roles"]}
    actor=c["actor"]
    if actor not in people or c["initiator"] not in people: raise ValueError("unknown person")
    if type(c["amount"]) is not int or c["amount"]<=0 or type(c["fundsAvailable"]) is not bool: raise ValueError("invalid budget")
    day=date.fromisoformat(c["as_of"])
    grants=[g for g in load("budget_authority_v1.json")["grants"] if g["person"]==actor and date.fromisoformat(g["valid_from"])<=day<=date.fromisoformat(g["valid_to"])]
    if len(grants)>1: raise ValueError("ambiguous grant")
    limit=grants[0]["limit"] if grants else None
    authorized=limit is not None and "budget.approve" in roles[people[actor]["role"]]["grants"]
    return dict(authorized=authorized,withinLimit=authorized and c["amount"]<=limit,limit=limit,manager=people[actor]["manager"])
def advance(c):
    if c["manager"] is None: raise ValueError("missing manager")
    return dict(actor=c["manager"])
OPERATIONS={"budget_authority":prepare,"advance_manager":advance}
