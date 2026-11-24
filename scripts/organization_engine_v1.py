"""Deterministic multi-organization structural fixture; no decision authority inferred."""
import random
def generate(seed=42,count=5):
    if type(count) is not int or not 1<=count<=1000: raise ValueError("invalid organization count")
    rng=random.Random(seed)
    organizations=[]
    for i in range(count):
        oid=f"ORG-{i+1:04d}"
        units=[dict(id=oid+":HQ",parent=None)]
        people=[dict(id=oid+":P1",unit=oid+":HQ",manager=None,role="director")]
        for j,kind in enumerate(("finance","technical","procurement"),2):
            uid=oid+":"+kind
            units.append(dict(id=uid,parent=oid+":HQ"))
            mid=oid+f":P{j}"
            people.append(dict(id=mid,unit=uid,manager=oid+":P1",role=kind+"_manager"))
            for k in range(rng.randint(2,5)):
                people.append(dict(id=mid+f".{k+1}",unit=uid,manager=mid,role=kind+"_specialist"))
        organizations.append(dict(id=oid,units=units,people=people))
    validate(organizations)
    return organizations
def validate(orgs):
    seen=set()
    for org in orgs:
        oid=org["id"]
        if oid in seen: raise ValueError("duplicate organization")
        seen.add(oid)
        for records,parent in ((org["units"],"parent"),(org["people"],"manager")):
            index={r["id"]:r for r in records}
            if len(index)!=len(records) or any(not k.startswith(oid+":") or k in seen for k in index): raise ValueError("invalid identity")
            seen.update(index)
            if sum(r[parent] is None for r in records)!=1: raise ValueError("invalid root count")
            for r in records:
                visited=set()
                current=r["id"]
                while current is not None:
                    if current in visited or current not in index: raise ValueError("invalid hierarchy")
                    visited.add(current)
                    current=index[current][parent]
        units={u["id"]:u for u in org["units"]}
        if any(p["unit"] not in units for p in org["people"]): raise ValueError("unknown unit")
    return True
