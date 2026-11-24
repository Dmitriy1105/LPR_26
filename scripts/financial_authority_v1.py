"""Evidence-backed financial approval bands. No currency conversion or implied authority."""
from datetime import date
PERMISSIONS=("approve","final_decision")
def _date(v):
    if not isinstance(v,str): raise ValueError("date must be ISO string")
    try: d=date.fromisoformat(v)
    except ValueError as e: raise ValueError("invalid ISO date") from e
    if d.isoformat()!=v: raise ValueError("date must use YYYY-MM-DD")
    return d
def validate_bands(org,bands):
    people={p["id"] for p in org["people"]}; ids=set()
    for b in bands:
        for k in ("band_id","org_id","person_id","action","permission","currency","min_amount","max_amount","valid_from","source_ref"):
            if k not in b: raise ValueError("missing band field: "+k)
        if b["org_id"]!=org["id"] or b["person_id"] not in people: raise ValueError("band subject outside organization")
        for k in ("band_id","action","currency","source_ref"):
            if not isinstance(b[k],str) or not b[k].strip(): raise ValueError("empty "+k)
        if b["band_id"] in ids: raise ValueError("duplicate band id")
        ids.add(b["band_id"])
        if b["permission"] not in PERMISSIONS: raise ValueError("invalid permission")
        if len(b["currency"])!=3 or not b["currency"].isalpha() or b["currency"]!=b["currency"].upper(): raise ValueError("currency must be ISO-style uppercase code")
        for k in ("min_amount","max_amount"):
            if isinstance(b[k],bool) or not isinstance(b[k],(int,float)): raise ValueError("amount must be numeric")
        if b["min_amount"]<0 or b["max_amount"]<b["min_amount"]: raise ValueError("invalid amount band")
        start=_date(b["valid_from"]); end=_date(b["valid_until"]) if b.get("valid_until") else None
        if end is not None and end<=start: raise ValueError("invalid validity interval")
        if b.get("status","active") not in ("active","revoked"): raise ValueError("invalid status")
        revoked=_date(b["revoked_at"]) if b.get("revoked_at") else None
        if revoked is not None and revoked<start: raise ValueError("revocation before start")
        if b.get("status","active")=="revoked" and revoked is None: raise ValueError("revoked band needs revoked_at")
    # Same person/action/permission/currency/date windows may not overlap in amount.
    for i,a in enumerate(bands):
        for z in bands[i+1:]:
            same=all(a[k]==z[k] for k in ("org_id","person_id","action","permission","currency"))
            if same and max(a["min_amount"],z["min_amount"])<=min(a["max_amount"],z["max_amount"]):
                a_end=_date(a["valid_until"]) if a.get("valid_until") else date.max
                z_end=_date(z["valid_until"]) if z.get("valid_until") else date.max
                if max(_date(a["valid_from"]),_date(z["valid_from"]))<min(a_end,z_end): raise ValueError("overlapping financial authority bands")
    return True
def evaluate_financial_authority(org,bands,person_id,action,permission,amount,currency,as_of):
    validate_bands(org,bands); d=_date(as_of)
    if person_id not in {p["id"] for p in org["people"]}: return {"authorized":False,"reason":"unknown_person"}
    if isinstance(amount,bool) or not isinstance(amount,(int,float)) or amount<0: raise ValueError("invalid amount")
    if not isinstance(currency,str) or len(currency)!=3 or currency!=currency.upper(): raise ValueError("invalid currency")
    matches=[]
    for b in bands:
        if (b["person_id"],b["action"],b["permission"],b["currency"])!=(person_id,action,permission,currency): continue
        if b.get("status","active")=="revoked" and d>=_date(b["revoked_at"]): continue
        if d<_date(b["valid_from"]) or (b.get("valid_until") and d>=_date(b["valid_until"])): continue
        if b.get("revoked_at") and d>=_date(b["revoked_at"]): continue
        if b["min_amount"]<=amount<=b["max_amount"]: matches.append(b)
    if len(matches)>1: raise ValueError("ambiguous financial authority")
    if not matches: return {"authorized":False,"reason":"no_matching_financial_band","currency":currency,"as_of":as_of}
    b=matches[0]
    return {"authorized":True,"reason":"matching_financial_band","band_id":b["band_id"],"currency":currency,"permission":permission,"as_of":as_of}
