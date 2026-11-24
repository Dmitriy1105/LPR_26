import json
from itertools import product
from universal_bpmn_engine import execute,ROOT
def main():
    registry=json.loads((ROOT/"models/process_registry_universal_v1.json").read_text())
    cases=[]
    for competent,technical,funds,limit,authorized in product((False,True),repeat=5):
        inputs=dict(competent=competent,technicalRequirementsMet=technical,remediable=False,budgetAuthorized=True,fundsAvailable=funds,withinLimit=limit,dealAuthorized=authorized,dealRequirementsMet=competent and technical and funds and limit)
        r=execute("corporate_decision",inputs,registry)
        assert r==execute("corporate_decision",inputs,registry)
        expected="deny" if not authorized else "approve" if inputs["dealRequirementsMet"] else "reject"
        assert r["result"]["context"]["dealOutcome"]==expected
        assert len(r["result"]["children"])==3
        assert [e["global_step"] for e in r["events"]]==list(range(len(r["events"])))
        assert len([e for e in r["events"] if e["event"]=="call_start"])==3
        assert len([e for e in r["events"] if e["event"]=="call_end"])==3
        cases.append(dict(inputs=inputs,outcome=expected))
    rejected=0
    for kwargs in (dict(max_depth=1),dict(max_events=2)):
        try: execute("corporate_decision",inputs,registry,**kwargs)
        except RuntimeError: rejected+=1
        else: raise AssertionError("limit not enforced")
    print(json.dumps(dict(status="PASS",cases=cases,limits_rejected=rejected),indent=2))
if __name__=="__main__": main()
