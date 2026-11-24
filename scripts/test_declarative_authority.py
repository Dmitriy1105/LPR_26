from registry_consolidation import compose
import json
from hashlib import sha256
from budget_policy_v1 import ROOT,load
from authority_execution_v1 import execute_authoritative,PROFILE
def main():
    p=load(PROFILE)
    specs={s["id"]:s for s in compose(p)["processes"]}
    assert set(specs)==set(p["allowed_inputs"])
    protected={"authorized","competent","withinLimit","dealAuthorized","budgetAuthorized"}
    for keys in p["allowed_inputs"].values(): assert not protected.intersection(keys)
    for pid,node,op in (("technical_expertise","assess","technical_authority"),("deal_approval","decide","deal_authority"),("budget_approval","decide","budget_authority")):
        assert specs[pid]["before"][node]==[op]
    cases=0
    for actor in ("P1","P2","P3","P4"):
        for pid,params in (("technical_expertise",dict(requirementsMet=True,remediable=False)),("deal_approval",dict(requirementsMet=True,revisionAllowed=False)),("budget_approval",dict(amount=100,as_of="2026-06-01",fundsAvailable=True))):
            inputs=dict(actor=actor,initiator="P4",**params)
            r=execute_authoritative(pid,inputs)
            assert r["authority_sources"][PROFILE]==sha256((ROOT/"models/organization"/PROFILE).read_bytes()).hexdigest()
            assert r==execute_authoritative(pid,inputs)
            cases+=1
    negatives=0
    for key in protected:
        try: execute_authoritative("deal_approval",dict(actor="P2",initiator="P4",requirementsMet=True,revisionAllowed=False,**{key:True}))
        except ValueError: negatives+=1
        else: raise AssertionError("authority override accepted")
    print(json.dumps(dict(status="PASS",cases=cases,negative_tests=negatives)))
if __name__=="__main__": main()
