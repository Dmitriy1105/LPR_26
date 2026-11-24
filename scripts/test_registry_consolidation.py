import json
from copy import deepcopy
from registry_consolidation import compose
from budget_policy_v1 import load
from authority_execution_v1 import PROFILE
def main():
    p=load(PROFILE)
    r=compose(p)
    assert len(r["processes"])==5
    assert r==compose(p)
    assert "registry" not in p
    cases=0
    for change in (lambda x:x["registry_overrides"].pop("deal_approval"),lambda x:x["registry_overrides"]["deal_approval"].update(bpmn="wrong"),lambda x:x["registry_overrides"]["corporate_multilevel_universal"]["calls"].pop("deal"),lambda x:x["registry_overrides"]["corporate_multilevel_universal"]["calls"]["deal"].update(process="budget_approval")):
        bad=deepcopy(p); change(bad)
        try: compose(bad)
        except ValueError: cases+=1
        else: raise AssertionError("invalid override accepted")
    print(json.dumps(dict(status="PASS",positive_cases=1,negative_cases=cases)))
if __name__=="__main__": main()
