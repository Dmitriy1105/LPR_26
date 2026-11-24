import json
from copy import deepcopy
from organization_engine_v1 import generate,validate
def main():
    orgs=generate()
    assert len(orgs)==5 and validate(orgs)
    assert all({u["department"] for u in o["units"]}>={"sales","finance","technical","procurement","legal","project_office","security","information_security"} for o in orgs)
    assert all(any(p["role"]=="security_manager" for p in o["people"]) and any(p["role"]=="information_security_manager" for p in o["people"]) for o in orgs)
    assert all(any(p["role"]=="head_of_sales" for p in o["people"]) and any(p["role"]=="account_manager" for p in o["people"]) for o in orgs)
    assert orgs==generate()
    assert orgs!=generate(seed=43)
    negatives=0
    for mutate in (lambda x:x.append(x[0]),lambda x:x[0]["people"].append(x[0]["people"][0]),lambda x:x[0]["people"][1].update(manager=x[1]["people"][0]["id"]),lambda x:x[0]["people"][1].update(manager=x[0]["people"][1]["id"]),lambda x:x[0]["people"][1].update(unit="unknown"),lambda x:x[0]["units"][1].update(parent=None),lambda x:x[0]["people"][1].update(manager="unknown"),lambda x:x[0]["units"].append(x[0]["units"][1])):
        bad=deepcopy(orgs); mutate(bad)
        try: validate(bad)
        except ValueError: negatives+=1
        else: raise AssertionError("invalid organization accepted")
    print(json.dumps(dict(status="PASS",organizations=len(orgs),people=sum(len(o["people"]) for o in orgs),positive_cases=3,negative_cases=negatives)))
if __name__=="__main__": main()
