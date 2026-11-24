import json
from copy import deepcopy
from organization_engine_v1 import generate
from temporal_authority_v1 import validate_grants,authorize_at
def grant(org,person,**kw):
    x=dict(grant_id="G1",org_id=org["id"],person_id=person,action="contract",permission="final_decision",valid_from="2026-01-01",valid_until="2026-12-31",max_amount=100000,source_ref="board-resolution-17",status="active")
    x.update(kw); return x
def main():
    org=generate(count=1)[0]; p=org["people"][0]["id"]; g=[grant(org,p)]
    assert validate_grants(org,g)
    assert authorize_at(org,g,p,"contract","final_decision","2026-06-01",90000)["authorized"]
    assert not authorize_at(org,g,p,"contract","final_decision","2025-12-31",100)["authorized"]
    assert not authorize_at(org,g,p,"contract","final_decision","2026-12-31",100)["authorized"]
    assert not authorize_at(org,g,p,"contract","final_decision","2026-06-01",100001)["authorized"]
    assert not authorize_at(org,g,p,"contract","approve","2026-06-01",100)["authorized"]
    revoked=[grant(org,p,revoked_at="2026-05-01")]
    assert authorize_at(org,revoked,p,"contract","final_decision","2026-04-30")["authorized"]
    assert not authorize_at(org,revoked,p,"contract","final_decision","2026-05-01")["authorized"]
    negatives=0
    for mutate in (lambda x:x[0].update(person_id="unknown"),lambda x:x[0].update(valid_until="2025-01-01"),lambda x:x[0].update(permission="influence"),lambda x:x[0].update(source_ref=""),lambda x:x[0].update(max_amount=-1),lambda x:x.append(x[0]),lambda x:x[0].update(revoked_at="2025-12-01"),lambda x:x[0].update(status="revoked")):
        bad=deepcopy(g); mutate(bad)
        try: validate_grants(org,bad)
        except ValueError: negatives+=1
        else: raise AssertionError("invalid grant accepted")
    print(json.dumps(dict(status="PASS",positive_cases=7,negative_cases=negatives)))
if __name__=="__main__": main()
