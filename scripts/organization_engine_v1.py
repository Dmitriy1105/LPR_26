"""Deterministic multi-organization model with six core departments."""
import random
DEPARTMENTS=("sales","finance","technical","procurement","legal","project_office","security","information_security")
SALES_ROLES=("corporate_sales_manager","account_manager","business_development_specialist","sales_specialist")
def generate(seed=42,count=5):
    if type(count) is not int or not 1<=count<=1000: raise ValueError("invalid organization count")
    rng=random.Random(seed); organizations=[]
    for i in range(count):
        oid=f"ORG-{i+1:04d}"
        units=[dict(id=oid+":HQ",parent=None,department="headquarters")]
        people=[dict(id=oid+":P1",unit=oid+":HQ",manager=None,role="director")]
        for j,kind in enumerate(DEPARTMENTS,2):
            uid=oid+":"+kind
            units.append(dict(id=uid,parent=oid+":HQ",department=kind))
            mid=oid+f":P{j}"
            manager_role="head_of_sales" if kind=="sales" else kind+"_manager"
            people.append(dict(id=mid,unit=uid,manager=oid+":P1",role=manager_role))
            for k in range(rng.randint(2,5)):
                role=(SALES_ROLES[k % len(SALES_ROLES)] if kind=="sales" else kind+"_specialist")
                people.append(dict(id=mid+f".{k+1}",unit=uid,manager=mid,role=role))
        organizations.append(dict(id=oid,units=units,people=people))
    validate(organizations); return organizations
def validate(orgs):
    seen=set()
    for org in orgs:
        oid=org["id"]
        if oid in seen: raise ValueError("duplicate organization")
        seen.add(oid)
        unit_index={u["id"]:u for u in org["units"]}
        people_index={p["id"]:p for p in org["people"]}
        for records,index,parent in ((org["units"],unit_index,"parent"),(org["people"],people_index,"manager")):
            if len(index)!=len(records) or any(not k.startswith(oid+":") or k in seen for k in index): raise ValueError("invalid identity")
            seen.update(index)
            if sum(r[parent] is None for r in records)!=1: raise ValueError("invalid root count")
            for r in records:
                visited=set(); current=r["id"]
                while current is not None:
                    if current in visited or current not in index: raise ValueError("invalid hierarchy")
                    visited.add(current); current=index[current][parent]
        if any(p["unit"] not in unit_index for p in org["people"]): raise ValueError("unknown unit")
        if any(p["manager"] is not None and p["manager"] not in people_index for p in org["people"]): raise ValueError("unknown manager")
        departments={u.get("department") for u in org["units"]}
        if not set(DEPARTMENTS)<=departments: raise ValueError("missing core department")
        sales=[p for p in org["people"] if p["unit"]==oid+":sales"]
        if not any(p["role"]=="head_of_sales" for p in sales) or not any(p["role"] in SALES_ROLES for p in sales): raise ValueError("incomplete sales department")
    return True
