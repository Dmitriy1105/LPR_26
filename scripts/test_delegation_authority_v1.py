import json
from copy import deepcopy
from organization_engine_v1 import generate
from temporal_authority_v1 import authorize_at
from delegation_authority_v1 import validate_delegations,authorize_delegated_at
def main():
    org=generate(count=1)[0]; a,b=org["people"][0]["id"],org["people"][1]["id"]
    g=[dict(grant_id="G1",org_id=org["id"],person_id=a,action="contract",permission="delegate",valid_from="2026-01-01",valid_until="2026-12-31",max_amount=50000,source_ref="board-resolution")]
    d=[dict(delegation_id="D1",org_id=org["id"],delegator_id=a,delegatee_id=b,source_grant_id="G1",action="contract",permission="approve",valid_from="2026-02-01",valid_until="2026-10-01",max_amount=20000,source_ref="delegation-order",redelegation=False)]
    assert validate_delegations(org,g,d)
    assert authorize_delegated_at(org,g,d,b,"contract","approve","2026-06-01",10000)["authorized"]
    assert not authorize_delegated_at(org,g,d,b,"contract","approve","2026-01-31",100)["authorized"]
    assert not authorize_delegated_at(org,g,d,b,"contract","approve","2026-10-01",100)["authorized"]
    assert not authorize_delegated_at(org,g,d,b,"contract","approve","2026-06-01",20001)["authorized"]
    assert not authorize_delegated_at(org,g,d,b,"contract","final_decision","2026-06-01",100)["authorized"]
    negatives=0
    for mutate in (lambda x:x[0].update(delegatee_id="unknown"),lambda x:x[0].update(delegator_id=b),lambda x:x[0].update(source_grant_id="missing"),lambda x:x[0].update(source_ref=""),lambda x:x[0].update(max_amount=60000),lambda x:x[0].update(redelegation=True),lambda x:x[0].update(valid_until="2026-01-01")):
        bad=deepcopy(d); mutate(bad)
        try: validate_delegations(org,g,bad)
        except ValueError: negatives+=1
        else: raise AssertionError("invalid delegation accepted")
    revoked=[dict(g[0],revoked_at="2026-05-01")]
    assert not authorize_delegated_at(org,revoked,d,b,"contract","approve","2026-06-01",100)["authorized"]
    print(json.dumps(dict(status="PASS",positive_cases=5,negative_cases=8)))
if __name__=="__main__": main()
