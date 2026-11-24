import json
from organization_engine_qc_v1 import audit
def main():
    a=audit(seed=42,count=5); b=audit(seed=42,count=5)
    assert a["status"]=="PASS" and a==b
    assert a["organizations"]==5 and len(a["organization_results"])==5
    assert all({"sales","security","information_security"}<=set(x["departments"]) for x in a["organization_results"])
    assert all(x["people"]>0 and x["roles"]==x["people"] for x in a["organization_results"])
    assert len(a["checks"])>=8 and all(a["checks"].values())
    print(json.dumps(dict(status="PASS",positive_cases=5,organizations=5,checks=len(a["checks"]))))
if __name__=="__main__": main()
