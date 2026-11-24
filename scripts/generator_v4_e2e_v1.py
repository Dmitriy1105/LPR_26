"""Generator v4 cross-layer E2E audit over organization engine and synthetic Bitrix24 contract fixtures."""
import json
from pathlib import Path
from organization_engine_qc_v1 import audit as organization_audit
from organization_integration_audit_v1 import audit as integration_audit
from bitrix24_rest_adapter_v1 import collect_pages

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/"src/data/bitrix24_contract_v1"
def _load(path):
    with path.open(encoding="utf-8") as stream: return json.load(stream)
def audit(seed=42,count=5):
    manifest=_load(FIXTURES/"manifest.json")
    org=organization_audit(seed=seed,count=count)
    integration=integration_audit()
    checks={"organization_engine":org["status"]=="PASS","organization_process_integration":integration["status"]=="PASS"}
    entities={}
    for method in manifest["methods"]:
        payloads=[_load(FIXTURES/item["file"]) for item in method["pages"]]
        parsed=collect_pages(method["method"],payloads)
        expected=method["recordCount"]
        entities[method["key"]]={"expected":expected,"actual":parsed["record_count"],"complete":parsed["complete"],"method":method["method"]}
        checks["bitrix24_"+method["key"]+"_count"]=parsed["record_count"]==expected
        checks["bitrix24_"+method["key"]+"_complete"]=parsed["complete"] is True
    checks["synthetic_fixture_declared"]=manifest.get("synthetic") is True
    checks["legacy_rest_profile_declared"]=manifest.get("profile")=="legacy-rest-v1"
    checks["no_live_api_claim"]=True
    return {"schema_version":"1.0","status":"PASS" if all(checks.values()) else "FAIL","seed":seed,"organization_count":count,"organization_audit":org,"integration_audit":integration,"bitrix24_fixture_profile":manifest.get("profile"),"synthetic":manifest.get("synthetic"),"entities":entities,"checks":checks,"passed":sum(checks.values()),"total":len(checks),"limitations":["E2E runs against committed synthetic fixtures, not a live Bitrix24 tenant.","Legacy /rest/ response profile only; REST 3.0 is not validated.","No OAuth/webhook credentials, live permission checks, rate limits or write-back are exercised.","Passing this audit proves the tested software and fixture contracts only, not production readiness."]}
def main():
    result=audit()
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    if result["status"]!="PASS": raise SystemExit(1)
if __name__=="__main__": main()
