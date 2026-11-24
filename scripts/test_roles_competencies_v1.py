import json
from copy import deepcopy
from organization_engine_v1 import generate
from roles_competencies_v1 import build,validate,add_competency
def main():
    org=generate(count=1)[0]; rows=build(org); assert validate(org,rows)
    sales=[r for r in rows if r["department"]=="sales"]
    assert any(r["position"]=="head_of_sales" for r in sales)
    assert any(r["position"]=="account_manager" for r in sales)
    assert any(r["position"]=="security_manager" and r["department"]=="security" for r in rows)
    assert any(r["position"]=="information_security_manager" and r["department"]=="information_security" for r in rows)
    assert any(r["position"]=="security_specialist" for r in rows)
    assert any(r["position"]=="information_security_specialist" for r in rows)
    enriched=add_competency(rows,sales[-1]["person_id"],"enterprise_sales","verified","assessment-001")
    assert validate(org,enriched)
    negatives=0
    for mutate in (lambda x:x.pop(),lambda x:x[0].update(position="finance_manager"),lambda x:x[0].update(authority_refs=["implied"]),lambda x:x[0]["competencies"].append({"skill":"x","evidence_status":"verified"}),lambda x:x[0].update(department="other")):
        bad=deepcopy(rows); mutate(bad)
        try: validate(org,bad)
        except ValueError: negatives+=1
        else: raise AssertionError("invalid role evidence accepted")
    try: add_competency(rows,"unknown","skill")
    except ValueError: negatives+=1
    else: raise AssertionError("unknown employee accepted")
    try: add_competency(rows,sales[-1]["person_id"],"unverified_test","verified")
    except ValueError: negatives+=1
    else: raise AssertionError("verified competency without source accepted")
    print(json.dumps(dict(status="PASS",people=len(rows),sales_roles=len(sales),positive_cases=3,negative_cases=negatives)))
if __name__=="__main__": main()
