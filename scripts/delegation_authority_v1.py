"""Scoped, evidence-backed delegation. No automatic redelegation or title-derived authority."""
from datetime import date
from temporal_authority_v1 import _date,validate_grants
def validate_delegations(org,grants,delegations):
    validate_grants(org,grants)
    people={p["id"] for p in org["people"]}; ids=set(); grant_index={g["grant_id"]:g for g in grants}
    for d in delegations:
        required=("delegation_id","org_id","delegator_id","delegatee_id","source_grant_id","action","permission","valid_from","source_ref")
        if any(k not in d for k in required): raise ValueError("missing delegation field")
        if d["org_id"]!=org["id"] or d["delegator_id"] not in people or d["delegatee_id"] not in people: raise ValueError("delegation party outside organization")
        if d["delegator_id"]==d["delegatee_id"]: raise ValueError("self delegation")
        for k in ("delegation_id","action","source_ref"):
            if not isinstance(d[k],str) or not d[k].strip(): raise ValueError("empty delegation field")
        if d["delegation_id"] in ids: raise ValueError("duplicate delegation id")
        ids.add(d["delegation_id"])
        source=grant_index.get(d["source_grant_id"])
        if source is None or source["person_id"]!=d["delegator_id"] or source["permission"]!="delegate" or source["action"]!=d["action"]: raise ValueError("delegator lacks matching delegation grant")
        if d["permission"] not in ("approve","final_decision"): raise ValueError("invalid delegated permission")
        start=_date(d["valid_from"]); end=_date(d["valid_until"]) if d.get("valid_until") else None
        if end is not None and end<=start: raise ValueError("invalid delegation interval")
        if start<_date(source["valid_from"]) or (source.get("valid_until") and (end is None or end>_date(source["valid_until"]))): raise ValueError("delegation exceeds source grant interval")
        cap=d.get("max_amount")
        if cap is not None and (isinstance(cap,bool) or not isinstance(cap,(int,float)) or cap<0): raise ValueError("invalid delegated amount cap")
        if source.get("max_amount") is not None and (cap is None or cap>source["max_amount"]): raise ValueError("delegation exceeds source amount cap")
        if d.get("redelegation",False) is not False: raise ValueError("redelegation is not supported")
    return True
def authorize_delegated_at(org,grants,delegations,delegatee_id,action,permission,as_of,amount=None):
    validate_delegations(org,grants,delegations); moment=_date(as_of)
    matches=[]
    for d in delegations:
        if (d["delegatee_id"],d["action"],d["permission"])!=(delegatee_id,action,permission): continue
        if moment<_date(d["valid_from"]) or (d.get("valid_until") and moment>=_date(d["valid_until"])): continue
        if d.get("revoked_at") and moment>=_date(d["revoked_at"]): continue
        if amount is not None and (isinstance(amount,bool) or not isinstance(amount,(int,float)) or amount<0): raise ValueError("invalid amount")
        if amount is not None and d.get("max_amount") is not None and amount>d["max_amount"]: continue
        source=next(g for g in grants if g["grant_id"]==d["source_grant_id"])
        if source.get("revoked_at") and moment>=_date(source["revoked_at"]): continue
        if source.get("status","active")=="revoked" and moment>=_date(source["revoked_at"]): continue
        matches.append(d)
    if len(matches)>1: raise ValueError("ambiguous delegated authority")
    if not matches: return dict(authorized=False,reason="no_matching_delegation")
    d=matches[0]
    return dict(authorized=True,reason="matching_delegation",delegation_id=d["delegation_id"],delegator_id=d["delegator_id"],delegatee_id=delegatee_id,permission=permission,as_of=as_of)
