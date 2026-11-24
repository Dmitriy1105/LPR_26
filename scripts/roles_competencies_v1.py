"""Separate formal position, evidenced competencies, authority and influence."""
from copy import deepcopy
ROLE_CATALOG={
 "director":{"department":"headquarters","level":"executive"},
 "head_of_sales":{"department":"sales","level":"manager"},
 "corporate_sales_manager":{"department":"sales","level":"specialist"},
 "account_manager":{"department":"sales","level":"specialist"},
 "business_development_specialist":{"department":"sales","level":"specialist"},
 "sales_specialist":{"department":"sales","level":"specialist"},
 "finance_manager":{"department":"finance","level":"manager"},
 "finance_specialist":{"department":"finance","level":"specialist"},
 "technical_manager":{"department":"technical","level":"manager"},
 "technical_specialist":{"department":"technical","level":"specialist"},
 "procurement_manager":{"department":"procurement","level":"manager"},
 "procurement_specialist":{"department":"procurement","level":"specialist"},
 "legal_manager":{"department":"legal","level":"manager"},
 "legal_specialist":{"department":"legal","level":"specialist"},
 "project_office_manager":{"department":"project_office","level":"manager"},
 "project_office_specialist":{"department":"project_office","level":"specialist"},
 "security_manager":{"department":"security","level":"manager"},
 "security_specialist":{"department":"security","level":"specialist"},
 "information_security_manager":{"department":"information_security","level":"manager"},
 "information_security_specialist":{"department":"information_security","level":"specialist"},
}
def build(org):
    people=[]
    for p in org["people"]:
        role=p["role"]
        if role not in ROLE_CATALOG: raise ValueError("unknown role")
        meta=ROLE_CATALOG[role]
        unit=next(u for u in org["units"] if u["id"]==p["unit"])
        if unit["department"]!=meta["department"]: raise ValueError("role department mismatch")
        people.append(dict(person_id=p["id"],position=role,department=meta["department"],level=meta["level"],competencies=[],authority_refs=[],influence_evidence=[]))
    return people
def validate(org,records):
    source={p["id"]:p for p in org["people"]}
    if len(records)!=len(source) or {r["person_id"] for r in records}!=set(source): raise ValueError("person coverage")
    for r in records:
        p=source[r["person_id"]]
        if r["position"]!=p["role"] or r["department"]!=next(u["department"] for u in org["units"] if u["id"]==p["unit"]): raise ValueError("position mismatch")
        if r.get("authority_refs") or r.get("influence_evidence"):
            raise ValueError("authority and influence require separately validated evidence")
        seen=set()
        for c in r["competencies"]:
            if not isinstance(c,dict) or not c.get("skill") or c.get("skill") in seen or c.get("evidence_status") not in ("verified","self_reported","unverified"): raise ValueError("invalid competency evidence")
            if c["evidence_status"]=="verified" and not c.get("source_ref"): raise ValueError("verified competency requires source evidence")
            if c.get("source_ref") is not None and (not isinstance(c["source_ref"],str) or not c["source_ref"].strip()): raise ValueError("invalid competency source")
            seen.add(c["skill"])
    return True
def add_competency(records,person_id,skill,evidence_status="unverified",source_ref=None):
    if evidence_status not in ("verified","self_reported","unverified") or not skill: raise ValueError("invalid competency")
    if evidence_status=="verified" and (not isinstance(source_ref,str) or not source_ref.strip()): raise ValueError("verified competency requires source evidence")
    if source_ref is not None and (not isinstance(source_ref,str) or not source_ref.strip()): raise ValueError("invalid competency source")
    out=deepcopy(records); target=next((r for r in out if r["person_id"]==person_id),None)
    if target is None: raise ValueError("unknown person")
    if any(c["skill"]==skill for c in target["competencies"]): raise ValueError("duplicate competency")
    item=dict(skill=skill,evidence_status=evidence_status)
    if source_ref is not None: item["source_ref"]=source_ref
    target["competencies"].append(item); return out
