"""Append-only organizational change ledger with deterministic historical projection."""
from copy import deepcopy
from datetime import date
KINDS=("hire","transfer","position_change","manager_change","termination")
def _date(v):
    if not isinstance(v,str): raise ValueError("effective_date must be ISO string")
    try: d=date.fromisoformat(v)
    except ValueError as e: raise ValueError("invalid effective_date") from e
    if d.isoformat()!=v: raise ValueError("date must use YYYY-MM-DD")
    return d
def validate_events(org,events):
    people={p["id"]:p for p in org["people"]}; units={u["id"] for u in org["units"]}; ids=set()
    for e in events:
        for k in ("event_id","org_id","person_id","kind","effective_date","source_ref"):
            if k not in e: raise ValueError("missing event field: "+k)
        if e["org_id"]!=org["id"] or e["person_id"] not in people: raise ValueError("event subject outside organization")
        for k in ("event_id","source_ref"):
            if not isinstance(e[k],str) or not e[k].strip(): raise ValueError("empty "+k)
        if e["event_id"] in ids: raise ValueError("duplicate event id")
        ids.add(e["event_id"])
        if e["kind"] not in KINDS: raise ValueError("invalid event kind")
        _date(e["effective_date"])
        if e["kind"] in ("transfer","hire") and e.get("new_unit") not in units: raise ValueError("unknown destination unit")
        if e["kind"]=="position_change" and not e.get("new_position"): raise ValueError("missing new position")
        if e["kind"]=="manager_change" and e.get("new_manager") not in people: raise ValueError("unknown new manager")
        if e["kind"]=="termination" and any(k in e for k in ("new_unit","new_position","new_manager")): raise ValueError("termination cannot assign new attributes")
    ordered=sorted(events,key=lambda e:(e["effective_date"],e["event_id"]))
    if events!=ordered: raise ValueError("events must be ordered by effective date and event id")
    return True
def project_at(org,events,as_of):
    validate_events(org,events); moment=_date(as_of)
    state={p["id"]:dict(person_id=p["id"],unit=p["unit"],position=p["role"],manager=p["manager"],active=True) for p in org["people"]}
    for e in events:
        if _date(e["effective_date"])>moment: break
        s=state[e["person_id"]]
        if e["kind"] in ("hire","transfer"): s["unit"]=e["new_unit"]; s["active"]=True
        if e["kind"]=="position_change": s["position"]=e["new_position"]
        if e["kind"]=="manager_change": s["manager"]=e["new_manager"]
        if e["kind"]=="termination": s["active"]=False
    return state
def append_event(events,event):
    out=deepcopy(events)
    if any(e["event_id"]==event.get("event_id") for e in out): raise ValueError("duplicate event id")
    out.append(deepcopy(event)); out.sort(key=lambda e:(e["effective_date"],e["event_id"])); return out
