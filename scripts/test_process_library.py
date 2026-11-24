import json
from itertools import product
from process_executor_v4 import ROOT,run
registry=json.loads((ROOT/"models/process_registry.json").read_text())
spec=next(p for p in registry["processes"] if p["id"]=="budget_approval")
cases=[]
for a,f,l in product([False,True],repeat=3):
    inputs=dict(authorized=a,fundsAvailable=f,withinLimit=l)
    expected="blocked" if not a else "rejected" if not f else "approved" if l else "escalated"
    result=run(spec,inputs)
    assert result["end"]==expected
    assert result==run(spec,inputs)
    cases.append({"inputs":inputs,**result})
budget_cases=list(cases); cases=[]

spec=next(p for p in registry["processes"] if p["id"]=="technical_expertise")
org=json.loads((ROOT/"models/organization/organization_profile_v1.json").read_text())
roles={r["id"]:r for r in org["roles"]}
people={p["id"]:p for p in org["people"]}
assert len(people)==len(org["people"])
assert all(p["role"] in roles and (p["manager"] is None or p["manager"] in people) for p in people.values())
for p in people.values():
    seen=set()
    while p["manager"] is not None:
        assert p["id"] not in seen
        seen.add(p["id"]); p=people[p["manager"]]
expert=roles[people["P2"]["role"]]
assert "technical.assess" in expert["competencies"] and "deal.approve" not in expert["grants"]
for c,m,r in product([False,True],repeat=3):
    inputs=dict(competent=c,requirementsMet=m,remediable=r)
    expected="referred" if not c else "positive" if m else "rework" if r else "negative"
    result=run(spec,inputs)
    assert result["end"]==expected and result==run(spec,inputs)
    assert not any(n["node_id"] in {"approve","reject"} for n in result["trace"])
    cases.append({"inputs":inputs,**result})
print(json.dumps({"budget_cases":budget_cases,"technical_cases":cases,"organization_checks":"PASS","status":"PASS"},indent=2))
