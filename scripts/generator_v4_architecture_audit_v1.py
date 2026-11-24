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
    authority_test=read_json("scenario-authority-enforcement-qc.json")
    bpmn_integration=read_json("generator-v4-bpmn-integration-qc.json")
    communication_test=read_json("scenario-communication-generator-qc.json")
    arch=read_json("reports/architecture_defect_registry.json")
    contract=(ROOT/"docs/GENERATOR_V4_DATA_CONTRACT.md").read_text(encoding="utf-8")
    scenario=(ROOT/"scripts/scenario_engine_v4.mjs").read_text(encoding="utf-8")
    communication_module=(ROOT/"scripts/scenario_communication_generator_v1.mjs").read_text(encoding="utf-8")
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
    scenario_has_communications=("generateCommunications" in communication_module and "DESCRIPTION" in communication_module and "SOURCE_EVENT_ID" in communication_module and communication_test.get("status")=="PASS" and communication_test.get("communications")==communication_test.get("source_events") and communication_test.get("deterministic") is True)
    scenario_has_ground_truth=any(k in scenario for k in ("ground_truth","gold_events","gold_labels"))
    e2e_runs_scenario=("scenario_engine_v4" in e2e or "process_executor_v4" in e2e or "authority_execution_v1" in e2e)
    contract_status=next((line.replace("**Status:**","",1).replace("Status:","",1).strip() for line in contract.splitlines() if line.startswith("**Status:**") or line.startswith("Status:")),"UNKNOWN")
    checks={
      "scenario_negative_test_pass":authority_test.get("status")=="PASS" and authority_test.get("negative_cases_passed")==authority_test.get("negative_cases") and authority_test.get("baseline",{}).get("pass") is True,
      "scenario_engine_emits_crm_communications":scenario_has_communications,
      "scenario_engine_emits_ground_truth":scenario_has_ground_truth,
      "e2e_executes_scenario_or_bpmn_runtime":bpmn_integration.get("status")=="PASS" and bpmn_integration.get("bpmn_dmn_executions")==bpmn_integration.get("deals") and bpmn_integration.get("matched_outcomes")==bpmn_integration.get("deals") and bpmn_integration.get("deterministic") is True,
      "data_contract_approved":contract_status.upper().startswith("APPROVED"),
      "fixture_count_matches_contract_baseline":target is not None and fixture_total==target,
      "architecture_partial_defects_closed":len(partial)==0,
      "restricted_bpmn_dmn_limitation_closed":len(limitations)==0,
      "bpmn_models_marked_executable":bool(bpmn_processes) and all(p["isExecutable"]=="true" for p in bpmn_processes),
    }
    findings=[
      {"id":"GEN-001","severity":"CRITICAL","status":"CLOSED" if checks["scenario_negative_test_pass"] else "OPEN","title":"Scenario Engine authority enforcement","evidence":f"scenario-authority-enforcement-qc.json: {authority_test.get('status')}; valid baseline={authority_test.get('baseline',{}).get('pass')}; rejected unauthorized/expired/wrong-scope/wrong-org cases={authority_test.get('negative_cases_passed')}/{authority_test.get('negative_cases')}. Legacy smoke report has negative_test.pass={smoke.get('negative_test',{}).get('pass')}, which is ambiguous without a separate assertion result.","impact":"GEN-001 is closed only when valid generated scenarios pass and every unauthorized mutation is rejected by the validator."},
      {"id":"GEN-002","severity":"HIGH","status":"CLOSED" if checks["e2e_executes_scenario_or_bpmn_runtime"] else "OPEN","title":"Scenario-to-BPMN/DMN execution bridge","evidence":f"generator-v4-bpmn-integration-qc.json: status={bpmn_integration.get('status')}; generated deals={bpmn_integration.get('deals')}; BPMN/DMN executions={bpmn_integration.get('bpmn_dmn_executions')}; matched outcomes={bpmn_integration.get('matched_outcomes')}; deterministic={bpmn_integration.get('deterministic')}.","impact":"Closes the seed-42 integration baseline. The actor mapping remains an explicit demo-profile mapping; dynamic mapping for arbitrary generated organizations remains a separate follow-up under ARCH-013/014."},
      {"id":"GEN-003","severity":"HIGH","status":"CLOSED" if checks["scenario_engine_emits_crm_communications"] else "OPEN","title":"Scenario-based CRM communication generation","evidence":f"scenario-communication-generator-qc.json: status={communication_test.get('status')}; source events={communication_test.get('source_events')}; rendered communications={communication_test.get('communications')}; linked events={communication_test.get('linked_source_events')}; channel counts={communication_test.get('channel_counts')}; deterministic={communication_test.get('deterministic')}.","impact":"Closes the seed-42 communication projection baseline. Text templates are deterministic synthetic examples; broader content diversity and realistic multi-turn dialogue remain future quality work."},
      {"id":"GEN-004","severity":"HIGH","status":"OPEN" if not checks["scenario_engine_emits_ground_truth"] else "CLOSED","title":"Scenario output has no linked Ground Truth event labels","evidence":"scripts/scenario_engine_v4.mjs output contains no ground_truth, gold_events or gold_labels field; the Data Contract describes these as required layers.","impact":"There is no scenario-linked gold record to independently assess who spoke, acted, approved, objected or executed."},
      {"id":"GEN-005","severity":"HIGH","status":"OPEN" if not checks["fixture_count_matches_contract_baseline"] else "CLOSED","title":"Synthetic CRM fixture count differs from declared regression baseline","evidence":f"Contract §8 explicitly leaves the legacy baseline unresolved (677 versus 767); current src/data/bitrix24_contract_v1/manifest.json sums to {fixture_total} records ({counts}). No canonical target is inferred.","impact":"Legacy fixture migration remains blocked until the 677/767 discrepancy is reconciled against an authoritative branch, commit and manifest."},
      {"id":"GEN-006","severity":"HIGH","status":"OPEN" if not checks["data_contract_approved"] else "CLOSED","title":"Generator v4 data contract is not approved","evidence":f"docs/GENERATOR_V4_DATA_CONTRACT.md status: {contract_status}.","impact":"The authoritative output schema and acceptance gates remain proposals; implementation cannot be certified against an accepted contract."},
      {"id":"GEN-007","severity":"HIGH","status":"OPEN" if not checks["architecture_partial_defects_closed"] else "CLOSED","title":"Prior architecture defects remain partially resolved","evidence":f"reports/architecture_defect_registry.json retains PARTIAL items: {', '.join(partial)}.","impact":"Independent full trace semantics, declarative bindings, negative coverage, generator authority integration, dynamic delegation and full replay remain incomplete."},
      {"id":"GEN-008","severity":"MEDIUM","status":"DECISION_REQUIRED" if not checks["restricted_bpmn_dmn_limitation_closed"] else "CLOSED","title":"BPMN/DMN execution is a restricted custom profile","evidence":f"reports/architecture_defect_registry.json retains LIMITATION items: {', '.join(limitations)}; docs/adr/0001-bpmn-dmn.md says models are descriptive and not executable-certified.","impact":"No general BPMN 2.0 / DMN 1.3 conformance claim is supported."},
      {"id":"GEN-009","severity":"MEDIUM","status":"DECISION_REQUIRED" if not checks["bpmn_models_marked_executable"] else "CLOSED","title":"BPMN model files are not declared executable","evidence":f"{sum(1 for p in bpmn_processes if p['isExecutable']=='false')} of {len(bpmn_processes)} parsed BPMN process definitions declare isExecutable=false.","impact":"The BPMN files currently serve as descriptive model inputs to a custom restricted runner, not independently executable BPMN process definitions."},
    ]
    return {
      "schema_version":"1.0",
      "audit":"Generator v4.0 Architecture & Data Quality Audit",
      "status":"REVIEW_REQUIRED" if any(x["status"]=="OPEN" for x in findings) else "PASS",
      "fixture_counts":counts,
      "fixture_total":fixture_total,
      "contract_baseline_target":target,
      "contract_status":contract_status,
      "scenario_smoke":smoke,
      "scenario_authority_enforcement":authority_test,
      "bpmn_dmn_integration":bpmn_integration,
      "communication_generation":communication_test,
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
