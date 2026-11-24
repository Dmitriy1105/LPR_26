"""Evidence-based architecture and data-quality audit for Generator v4.0."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read_json(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def audit():
    manifest=read_json("src/data/bitrix24_contract_v1/manifest.json")
    smoke=read_json("reports/scenario_engine_v4_smoke.json")
    arch=read_json("reports/architecture_defect_registry.json")
    contract=(ROOT/"docs/GENERATOR_V4_DATA_CONTRACT.md").read_text(encoding="utf-8")
    scenario=(ROOT/"scripts/scenario_engine_v4.mjs").read_text(encoding="utf-8")
    e2e=(ROOT/"scripts/generator_v4_e2e_v1.py").read_text(encoding="utf-8")
    counts=manifest.get("recordCounts",{})
    fixture_total=sum(v for v in counts.values() if isinstance(v,int))
    target_match=re.search(r"(\d+)\s*-record baseline",contract,re.I)
    target=int(target_match.group(1)) if target_match else None
    process_files=sorted((ROOT/"models/bpmn").glob("*.bpmn"))
    bpmn_processes=[]
    ns="{http://www.omg.org/spec/BPMN/20100524/MODEL}"
    for path in process_files:
        root=ET.parse(path).getroot()
        for process in root.findall(ns+"process"):
            bpmn_processes.append({"file":str(path.relative_to(ROOT)),"id":process.get("id"),"isExecutable":process.get("isExecutable")})
    partial=[x["id"] for x in arch.get("defects",[]) if x.get("status")=="PARTIAL"]
    limitations=[x["id"] for x in arch.get("defects",[]) if x.get("status")=="LIMITATION"]
    returns_scenario_payload="return {version:VERSION,seed,organizations:orgs,people,grants,deals,events}" in scenario.replace("\n"," ")
    scenario_has_communications=any(k in scenario for k in ("communications","activities","transcripts","emails","meetings"))
    scenario_has_ground_truth=any(k in scenario for k in ("ground_truth","gold_events","gold_labels"))
    e2e_runs_scenario=("scenario_engine_v4" in e2e or "process_executor_v4" in e2e or "authority_execution_v1" in e2e)
    contract_status=contract.splitlines()[1].strip() if len(contract.splitlines())>1 else "UNKNOWN"
    checks={
      "scenario_negative_test_pass":bool(smoke.get("negative_test",{}).get("pass")),
      "scenario_engine_emits_crm_communications":scenario_has_communications,
      "scenario_engine_emits_ground_truth":scenario_has_ground_truth,
      "e2e_executes_scenario_or_bpmn_runtime":e2e_runs_scenario,
      "data_contract_approved":contract_status.lower().endswith("approved"),
      "fixture_count_matches_contract_baseline":target is not None and fixture_total==target,
      "architecture_partial_defects_closed":len(partial)==0,
      "restricted_bpmn_dmn_limitation_closed":len(limitations)==0,
      "bpmn_models_marked_executable":bool(bpmn_processes) and all(p["isExecutable"]=="true" for p in bpmn_processes),
    }
    findings=[
      {"id":"GEN-001","severity":"CRITICAL","status":"OPEN" if not checks["scenario_negative_test_pass"] else "CLOSED","title":"Scenario Engine negative authorization case fails","evidence":"reports/scenario_engine_v4_smoke.json: negative_test.pass=false; error unauthorized decision ORG-1-D1-E9","impact":"A generated decision can violate the intended authority policy; scenario output is not safe to treat as BPMN/DMN-conformant."},
      {"id":"GEN-002","severity":"HIGH","status":"OPEN" if not checks["e2e_executes_scenario_or_bpmn_runtime"] else "CLOSED","title":"End-to-end audit does not execute Generator v4 scenario runtime","evidence":"scripts/generator_v4_e2e_v1.py imports organization_engine_qc_v1, organization_integration_audit_v1 and bitrix24_rest_adapter_v1; it does not invoke scenario_engine_v4.mjs, process_executor_v4.py or authority_execution_v1.py.","impact":"Current E2E PASS does not demonstrate BPMN/DMN-to-scenario-to-event generation."},
      {"id":"GEN-003","severity":"HIGH","status":"OPEN" if not checks["scenario_engine_emits_crm_communications"] else "CLOSED","title":"Scenario engine does not render CRM communication records","evidence":"scripts/scenario_engine_v4.mjs returns organizations, people, grants, deals and events; it has no communication/activity/email/call/meeting projection.","impact":"Business-process events are not yet transformed into the CRM communication dataset used for downstream analysis."},
      {"id":"GEN-004","severity":"HIGH","status":"OPEN" if not checks["scenario_engine_emits_ground_truth"] else "CLOSED","title":"Scenario output has no linked Ground Truth event labels","evidence":"scripts/scenario_engine_v4.mjs output contains no ground_truth, gold_events or gold_labels field; the Data Contract describes these as required layers.","impact":"There is no scenario-linked gold record to independently assess who spoke, acted, approved, objected or executed."},
      {"id":"GEN-005","severity":"HIGH","status":"OPEN" if not checks["fixture_count_matches_contract_baseline"] else "CLOSED","title":"Synthetic CRM fixture count differs from declared regression baseline","evidence":f"docs/GENERATOR_V4_DATA_CONTRACT.md declares {target} records; src/data/bitrix24_contract_v1/manifest.json sums to {fixture_total} records ({counts}).","impact":"The documented v4 regression baseline is not reproduced by the committed fixture manifest."},
      {"id":"GEN-006","severity":"HIGH","status":"OPEN" if not checks["data_contract_approved"] else "CLOSED","title":"Generator v4 data contract is not approved","evidence":f"docs/GENERATOR_V4_DATA_CONTRACT.md status: {contract_status}.","impact":"The authoritative output schema and acceptance gates remain proposals; implementation cannot be certified against an accepted contract."},
      {"id":"GEN-007","severity":"HIGH","status":"OPEN" if not checks["architecture_partial_defects_closed"] else "CLOSED","title":"Prior architecture defects remain partially resolved","evidence":f"reports/architecture_defect_registry.json retains PARTIAL items: {', '.join(partial)}.","impact":"Independent full trace semantics, declarative bindings, negative coverage, generator authority integration, dynamic delegation and full replay remain incomplete."},
      {"id":"GEN-008","severity":"MEDIUM","status":"OPEN" if not checks["restricted_bpmn_dmn_limitation_closed"] else "CLOSED","title":"BPMN/DMN execution is a restricted custom profile","evidence":f"reports/architecture_defect_registry.json retains LIMITATION items: {', '.join(limitations)}; docs/adr/0001-bpmn-dmn.md says models are descriptive and not executable-certified.","impact":"No general BPMN 2.0 / DMN 1.3 conformance claim is supported."},
      {"id":"GEN-009","severity":"MEDIUM","status":"OPEN" if not checks["bpmn_models_marked_executable"] else "CLOSED","title":"BPMN model files are not declared executable","evidence":f"{sum(1 for p in bpmn_processes if p['isExecutable']=='false')} of {len(bpmn_processes)} parsed BPMN process definitions declare isExecutable=false.","impact":"The BPMN files currently serve as descriptive model inputs to a custom restricted runner, not independently executable BPMN process definitions."},
    ]
    return {
      "schema_version":"1.0",
      "audit":"Generator v4.0 Architecture & Data Quality Audit",
      "status":"REVIEW_REQUIRED" if any(x["status"]=="OPEN" for x in findings) else "PASS",
      "fixture_counts":counts,
      "fixture_total":fixture_total,
      "contract_baseline_target":target,
      "scenario_smoke":smoke,
      "bpmn_processes":bpmn_processes,
      "prior_architecture_partial_ids":partial,
      "prior_architecture_limitation_ids":limitations,
      "checks":checks,
      "findings":findings,
      "scope_note":"This is a source-and-report audit of the committed branch. It does not claim that unexecuted code paths were runtime-tested. Findings are evidence-linked and require triage before remediation."
    }

def main():
    result=audit()
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
    # REVIEW_REQUIRED is an expected audit result, not a failing CI job.
    if result["status"] not in ("PASS","REVIEW_REQUIRED"):
        raise SystemExit(1)

if __name__=="__main__":
    main()
