"""Fail closed on malformed organizational and budget authority data."""
from datetime import date
def validate(org,budget):
    people={p["id"]:p for p in org["people"]}
    roles={r["id"]:r for r in org["roles"]}
    if len(people)!=len(org["people"]) or len(roles)!=len(org["roles"]): raise ValueError("duplicate organization ID")
    for p in people.values():
        if p["role"] not in roles: raise ValueError("unknown role")
        seen=set(); current=p["id"]
        while current is not None:
            if current in seen or current not in people: raise ValueError("invalid hierarchy")
            seen.add(current); current=people[current]["manager"]
    if budget["currency"]!="RUB": raise ValueError("unsupported currency")
    periods={}
    for g in budget["grants"]:
        actor=g["person"]
        if actor not in people or "budget.approve" not in roles[people[actor]["role"]]["grants"]: raise ValueError("invalid grant subject")
        if type(g["limit"]) is not int or g["limit"]<=0: raise ValueError("invalid limit")
        a,b=date.fromisoformat(g["valid_from"]),date.fromisoformat(g["valid_to"])
        if a>b: raise ValueError("invalid grant period")
        for x,y in periods.get(actor,[]):
            if a<=y and x<=b: raise ValueError("overlapping grants")
        periods.setdefault(actor,[]).append((a,b))
