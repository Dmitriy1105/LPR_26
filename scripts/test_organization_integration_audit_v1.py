import json
from organization_integration_audit_v1 import audit
def main():
    r=audit()
    assert r["status"]=="PASS" and r["passed"]==r["total"]==8
    assert all(r["checks"].values())
    assert len(r["limitations"])==3
    print(json.dumps(dict(status="PASS",positive_cases=8,limitations=3)))
if __name__=="__main__": main()
