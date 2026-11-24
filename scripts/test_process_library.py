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
print(json.dumps({"process":spec["id"],"cases":cases,"status":"PASS"},indent=2))
