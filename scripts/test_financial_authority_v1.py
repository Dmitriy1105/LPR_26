import json
from copy import deepcopy
from organization_engine_v1 import generate
from financial_authority_v1 import validate_bands,evaluate_financial_authority
def band(org,p,**kw):
    b=dict(band_id="B1",org_id=org["id"],person_id=p,action="contract",permission="approve",currency="SGD",min_amount=0,max_amount=100000,valid_from="2026-01-01",valid_until="2027-01-01",source_ref="policy-2026-01")
    b.update(kw); return b
def main():
    org=generate(count=1)[0]; p=org["people"][0]["id"]; bands=[band(org,p)]
    assert validate_bands(org,bands)
    assert evaluate_financial_authority(org,bands,p,"contract","approve",0,"SGD","2026-06-01")["authorized"]
    assert evaluate_financial_authority(org,bands,p,"contract","approve",100000,"SGD","2026-06-01")["authorized"]
    assert not evaluate_financial_authority(org,bands,p,"contract","approve",100001,"SGD","2026-06-01")["authorized"]
    assert not evaluate_financial_authority(org,bands,p,"contract","approve",10,"USD","2026-06-01")["authorized"]
    assert not evaluate_financial_authority(org,bands,p,"contract","approve",10,"SGD","2027-01-01")["authorized"]
    assert not evaluate_financial_authority(org,bands,p,"contract","final_decision",10,"SGD","2026-06-01")["authorized"]
    negatives=0
    for mutate in (lambda x:x[0].update(person_id="unknown"),lambda x:x[0].update(currency="sgd"),lambda x:x[0].update(max_amount=-1),lambda x:x[0].update(valid_until="2025-01-01"),lambda x:x[0].update(source_ref=""),lambda x:x.append(x[0]),lambda x:x[0].update(permission="influence"),lambda x:x[0].update(status="revoked")):
        bad=deepcopy(bands); mutate(bad)
        try: validate_bands(org,bad)
        except ValueError: negatives+=1
        else: raise AssertionError("invalid financial band accepted")
    overlap=[band(org,p),band(org,p,band_id="B2",min_amount=50000,max_amount=150000)]
    try: validate_bands(org,overlap)
    except ValueError: negatives+=1
    else: raise AssertionError("overlapping bands accepted")
    print(json.dumps(dict(status="PASS",positive_cases=6,negative_cases=negatives)))
if __name__=="__main__": main()
