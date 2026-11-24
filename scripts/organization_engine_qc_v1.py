"""Cross-module Organization Engine QC and machine-readable baseline audit."""
import json
from organization_engine_v1 import generate,validate,DEPARTMENTS
from roles_competencies_v1 import build,validate as validate_roles
from temporal_authority_v1 import validate_grants
from financial_authority_v1 import validate_bands
from delegation_authority_v1 import validate_delegations
from organizational_changes_v1 import validate_events as validate_org_events,project_at
from event_chronology_v1 import validate_events as validate_chronology
def audit(seed=42,count=5):
    orgs=generate(seed=seed,count=count); validate(orgs)
    report={"schema_version":"1.0","status":"PASS","organizations":len(orgs),"departments_required":list(DEPARTMENTS),"checks":{},"organization_results":[]}
    checks={"deterministic_generation":generate(seed=seed,count=count)==generate(seed=seed,count=count),"unique_organization_ids":len({o["id"] for o in orgs})==len(orgs),"department_coverage":True,"sales_department_coverage":True,"security_separation":True,"role_coverage":True,"competency_evidence_defaults":True,"authority_empty_by_default":True,"cross_module_empty_ledger_compatibility":True}
    for org in orgs:
        departments={u["department"] for u in org["units"]}
        checks["department_coverage"] &= set(DEPARTMENTS)<=departments
        checks["security_separation"] &= {"security","information_security"}<=departments
        sales=[p for p in org["people"] if next(u for u in org["units"] if u["id"]==p["unit"])["department"]=="sales"]
        checks["sales_department_coverage"] &= any(p["role"]=="head_of_sales" for p in sales) and any(p["role"]=="account_manager" for p in sales)
        roles=build(org); checks["role_coverage"] &= validate_roles(org,roles) is True and len(roles)==len(org["people"])
        checks["competency_evidence_defaults"] &= all(not r["competencies"] for r in roles)
        checks["authority_empty_by_default"] &= all(not r["authority_refs"] and not r["influence_evidence"] for r in roles)
        empty_grants=[]; empty_bands=[]; empty_delegations=[]; empty_events=[]; empty_chronology=[]
        checks["cross_module_empty_ledger_compatibility"] &= validate_grants(org,empty_grants) and validate_bands(org,empty_bands) and validate_delegations(org,empty_grants,empty_delegations) and validate_org_events(org,empty_events) and validate_chronology(empty_chronology) and isinstance(project_at(org,empty_events,"2026-01-01"),dict)
        report["organization_results"].append({"organization_id":org["id"],"units":len(org["units"]),"people":len(org["people"]),"departments":sorted(departments),"roles":len(roles),"status":"PASS"})
    report["checks"]= {k:bool(v) for k,v in checks.items()}
    report["failed_checks"]=[k for k,v in report["checks"].items() if not v]
    report["status"]="PASS" if all(report["checks"].values()) else "FAIL"
    return report
def main():
    result=audit(); print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    if result["status"]!="PASS": raise SystemExit(1)
if __name__=="__main__": main()
