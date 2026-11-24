"""GEN-010.8 canonical composite BPMN execution over Generator v4 QC worlds.

Executes corporate_multilevel_universal recursively through registered callActivities.
Financial limits remain synthetic scenario inputs because v4 canonical data currently
has no amount/budget-band entity. The report states this limitation explicitly.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from generator_v4_scenario_engine_v1 import build as build_scenario, _staff_index
from generator_v4_authority_adapter_v1 import to_legacy_org
from temporal_authority_v1 import authorize_at
from process_executor_composite_v1 import run_composite

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT/"config/generator_v4_0.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT/"models/process_registry.json").read_text(encoding="utf-8"))
ROOT_PROCESS = next(p for p in REGISTRY["processes"] if p["id"]=="corporate_multilevel_universal")


def _grants_for_org(org, grants):
    rows=[]
    for g in grants:
        if g["organization_id"] != org["organization_id"]:
            continue
        if g["scope"] == "deal_approval":
            action, permission = "approve_deal", "final_decision"
        elif g["scope"].startswith("unit_approval:"):
            action, permission = "approve_unit", "approve"
        else:
            raise ValueError("unsupported authority scope " + g["scope"])
        rows.append({"grant_id":g["grant_id"],"org_id":org["organization_id"],
            "person_id":g["contact_id"],"action":action,"permission":permission,
            "valid_from":g["valid_from"][:10],"valid_until":None,"revoked_at":None,
            "status":"active","source_ref":g["source_ref"]})
    return rows


def _authorized(org, grants, actor, action, permission, date):
    return authorize_at(to_legacy_org(org), grants, actor, action, permission, date)


def _flatten(trace, prefix=""):
    rows=[]
    for node in trace:
        path = prefix + node["node_id"]
        rows.append({"path":path,"node_id":node["node_id"],"type":node["type"],
                     "process_id":None})
        for child in node.get("child_trace",[]):
            rows.extend(_flatten([child], prefix + node["node_id"] + "/"))
    return rows


def audit():
    world=build_scenario(config=CONFIG)
    orgs={o["organization_id"]:o for o in world["organizations"]}
    grants_by_org={oid:_grants_for_org(org,world["authority_grants"]) for oid,org in orgs.items()}
    events_by_deal={}
    for e in world["events"]:
        events_by_deal.setdefault(e["deal_id"],[]).append(e)
    staff_by_org={oid:_staff_index(org) for oid,org in orgs.items()}
    rows=[]; errors=[]; unit_checks=0; unit_errors=0; terminals=Counter(); final_reconciliations=0; close_reconciliations=0
    for deal in world["deals"]:
        oid=deal["organization_id"]; org=orgs[oid]; staff=staff_by_org[oid]
        events=sorted(events_by_deal[deal["deal_id"]],key=lambda e:e["occurred_at"])
        as_of=events[0]["occurred_at"][:10]
        director=staff["director"]; finance=staff["managers"]["finance"]
        sales=staff["sales_initiator"]; technical=staff["managers"]["technical"]
        director_auth=_authorized(org,grants_by_org[oid],director,"approve_deal","final_decision",
                                  next(e["occurred_at"][:10] for e in events if e["event_type"] in ("approve","reject")))
        if not director_auth.get("authorized"):
            errors.append({"deal_id":deal["deal_id"],"error":"final_authority_denied"})
        # Each recorded unit approval must independently resolve to its exact grant.
        for event in [e for e in events if e["event_type"]=="unit_approval"]:
            result=_authorized(org,grants_by_org[oid],event["actor_contact_id"],
                               "approve_unit","approve",event["occurred_at"][:10])
            unit_checks+=1
            if not result.get("authorized") or result.get("grant_id")!=event["authority_grant_ref"]:
                unit_errors+=1
                errors.append({"event_id":event["event_id"],"error":"unit_authority_mismatch"})
        final_events=[e for e in events if e["event_type"] in ("approve","reject")]
        close_events=[e for e in events if e["event_type"]=="close"]
        if len(final_events)!=1 or final_events[0]["actor_contact_id"]!=director:
            errors.append({"deal_id":deal["deal_id"],"error":"event_final_decision_actor_mismatch"})
        else:
            final_reconciliations+=1
        if len(close_events)!=1 or close_events[0]["decision_outcome"]!=deal["status"]:
            errors.append({"deal_id":deal["deal_id"],"error":"event_close_outcome_mismatch"})
        else:
            close_reconciliations+=1
        family=deal["family"]
        def budget_authority(context):
            # Unit-level finance authorization is checked from canonical grants.
            result=_authorized(org,grants_by_org[oid],context["actor"],
                               "approve_unit","approve",context["as_of"])
            return {"authorized":bool(result.get("authorized")),
                    "withinLimit":True,"fundsAvailable":True,
                    "hasManager":org_person_manager.get(context["actor"]) is not None,
                    "authority_grant_id":result.get("grant_id")}
        def advance_manager(context):
            manager=org_person_manager.get(context["actor"])
            if manager is None:
                raise ValueError("budget escalation has no next manager")
            return {"actor":manager}
        org_person_manager={p["contact_id"]:p["manager_contact_id"] for p in org["people"]}
        hooks={"budget_escalation_universal":{
            "budget_authority":budget_authority,
            "advance_manager":advance_manager
        }}
        hooks["__process_hooks__"]={"budget_escalation_universal":hooks["budget_escalation_universal"]}
        inputs={
            "competent":True,
            "technicalRequirementsMet":family!="rejected",
            "remediable":False,
            "amount":1,
            "fundsAvailable":True,
            "as_of":as_of,
            "initiator":sales,
            "budgetActor":finance,
            "dealAuthorized":bool(director_auth.get("authorized")),
            "dealRequirementsMet":family not in ("rejected","conflict_revision"),
            "revisionAllowed":family=="conflict_revision"
        }
        # The corporate registry maps technical and budget call results to
        # technicalStatus/budgetStatus. The finance hook checks an actual
        # finance-unit grant; monetary ceiling/funds remain synthetic inputs.
        try:
            result=run_composite(ROOT_PROCESS,inputs,REGISTRY,hooks)
        except Exception as exc:
            errors.append({"deal_id":deal["deal_id"],"error":"composite_execution_error","detail":str(exc)})
            continue
        terminal=result["end"]; terminals[terminal]+=1
        expected="end"
        outcome=result["context"].get("dealOutcome")
        expected_outcome="reject" if family=="rejected" else "approve"
        if terminal!=expected:
            errors.append({"deal_id":deal["deal_id"],"error":"terminal_mismatch","expected":expected,"actual":terminal})
        if outcome!=expected_outcome:
            errors.append({"deal_id":deal["deal_id"],"error":"decision_outcome_mismatch","expected":expected_outcome,"actual":outcome})
        if result["context"].get("budgetStatus")!="approved":
            errors.append({"deal_id":deal["deal_id"],"error":"budget_subprocess_not_approved",
                           "actual":result["context"].get("budgetStatus")})
        if family=="conflict_revision":
            deal_child=next((n for n in result["trace"] if n["node_id"]=="deal"),None)
            nested=deal_child.get("child_trace",[]) if deal_child else []
            ids=[n["node_id"] for n in nested]
            if "object" not in ids or "revise" not in ids or "recheck" not in ids:
                errors.append({"deal_id":deal["deal_id"],"error":"revision_path_not_executed"})
        rows.append({"deal_id":deal["deal_id"],"organization_id":oid,"family":family,
            "terminal":terminal,"deal_outcome":outcome,
            "technical_status":result["context"].get("technicalStatus"),
            "budget_status":result["context"].get("budgetStatus"),
            "readiness":result["context"].get("readiness"),
            "root_trace":result["trace"]})
    expected_unit=sum(1 for e in world["events"] if e["event_type"]=="unit_approval")
    family_counts=dict(Counter(r["family"] for r in rows))
    outcome_counts=dict(Counter(r["deal_outcome"] for r in rows))
    return {"status":"PASS" if not errors and len(rows)==800 and unit_checks==expected_unit else "FAIL",
        "seed":world["seed"],"organizations":len(orgs),"deals":len(world["deals"]),
        "composite_executions":len(rows),"unit_approval_authority_checks":unit_checks,
        "unit_approval_authority_expected":expected_unit,"unit_authority_errors":unit_errors,
        "final_decision_event_reconciliations":final_reconciliations,
        "deal_close_event_reconciliations":close_reconciliations,
        "terminal_distribution":dict(terminals),"scenario_family_counts":family_counts,\n        "deal_outcome_counts":outcome_counts,"errors":errors,"results":rows,
        "process_id":ROOT_PROCESS["id"],"nested_call_activity_execution":True,
        "financial_policy_evidence":"SYNTHETIC_INPUTS_ONLY_NO_CANONICAL_BUDGET_BANDS",
        "communication_rendering":"NOT_IN_SCOPE_GEN_010_9",
        "generation_authorized":CONFIG["generation_authorized"],
        "bulk_generation_enabled":CONFIG["bulk_generation_enabled"]}


if __name__=="__main__":
    report=audit()
    print(json.dumps({k:v for k,v in report.items() if k!="results"},
                     ensure_ascii=False,indent=2,sort_keys=True))
    if report["status"]!="PASS":
        raise SystemExit(1)
