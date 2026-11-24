"""Evidence-backed temporal authority grants; no authority inferred from job title."""
from datetime import date
PERMISSIONS=("approve","final_decision","delegate")
def _date(value):
    if not isinstance(value,str): raise ValueError("date must be ISO string")
    try: parsed=date.fromisoformat(value)
    except ValueError as exc: raise ValueError("invalid ISO date") from exc
    if parsed.isoformat()!=value: raise ValueError("date must use YYYY-MM-DD")
    return parsed
def validate_grants(org,grants):
    people={p["id"] for p in org["people"]}; ids=set()
    for g in grants:
        required=("grant_id","org_id","person_id","action","permission","valid_from","source_ref")
        if any(k not in g for k in required): raise ValueError("missing grant field")
        if g["org_id"]!=org["id"] or g["person_id"] not in people: raise ValueError("grant subject outside organization")
        if not all(isinstance(g[k],str) and g[k].strip() for k in ("grant_id","action","source_ref")): raise ValueError("empty grant identity, action or evidence")
        if g["grant_id"] in ids: raise ValueError("duplicate grant id")
        ids.add(g["grant_id"])
        if g["permission"] not in PERMISSIONS: raise ValueError("invalid permission")
        start=_date(g["valid_from"]); end=_date(g["valid_until"]) if g.get("valid_until") is not None else None
        revoked=_date(g["revoked_at"]) if g.get("revoked_at") is not None else None
        if end is not None and end<=start: raise ValueError("invalid validity interval")
        if revoked is not None and revoked<start: raise ValueError("revocation before grant")
        amount=g.get("max_amount")
        if amount is not None and (isinstance(amount,bool) or not isinstance(amount,(int,float)) or amount<0): raise ValueError("invalid amount ceiling")
        if g.get("status","active") not in ("active","revoked"): raise ValueError("invalid grant status")
        if g.get("status","active")=="revoked" and revoked is None: raise ValueError("revoked grant needs revoked_at")
    return True
def authorize_at(org,grants,person_id,action,permission,as_of,amount=None):
    validate_grants(org,grants); moment=_date(as_of)
    if person_id not in {p["id"] for p in org["people"]}: return dict(authorized=False,reason="unknown_person")
    if permission not in PERMISSIONS: raise ValueError("invalid permission")
    if amount is not None and (isinstance(amount,bool) or not isinstance(amount,(int,float)) or amount<0): raise ValueError("invalid amount")
    for g in grants:
        if g["person_id"]!=person_id or g["action"]!=action or g["permission"]!=permission: continue
        if g["status"]=="revoked" and moment>=_date(g["revoked_at"]): continue
        if moment<_date(g["valid_from"]): continue
        if g.get("valid_until") is not None and moment>=_date(g["valid_until"]): continue
        if g.get("revoked_at") is not None and moment>=_date(g["revoked_at"]): continue
        if amount is not None and g.get("max_amount") is not None and amount>g["max_amount"]: continue
        return dict(authorized=True,reason="matching_temporal_grant",grant_id=g["grant_id"],permission=permission,as_of=as_of)
    return dict(authorized=False,reason="no_matching_temporal_grant",permission=permission,as_of=as_of)
