"""Canonical v4.0 scenario engine over the approved Organization Engine output.

This module creates in-memory QC worlds only. It never writes CRM fixtures or enables
bulk generation. Observable projections and hidden Ground Truth are separate objects.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from generator_v4_organization_adapter_v1 import build as build_organizations

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "generator_v4_0.json"
SCHEMA_VERSION = "1.0.0"
FAMILY_ORDER = ("routine_approval", "conflict_revision", "rejected", "multi_level_approval")
EVENT_TYPES = {
    "request_information", "delegate", "complete_task", "review", "recommend",
    "object", "revise", "unit_approval", "approve", "reject", "close"
}
ELIGIBLE_MISSING_FIELDS = ("target_contact_id", "context_note")


def _load_config(config=None):
    if config is not None:
        return config
    return json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))


def _family_plan(config):
    families = config["scenario_families"]
    plan = {row["code"]: row["exact_count"] for row in families}
    if set(plan) != set(FAMILY_ORDER) or sum(plan.values()) != config["total_deals"]:
        raise ValueError("scenario family contract is incomplete or inconsistent")
    for row in families:
        if row["exact_count"] * 100 != config["total_deals"] * row["share_percent"]:
            raise ValueError("scenario family exact count/share mismatch: " + row["code"])
    return plan


def _staff_index(org):
    people = {p["contact_id"]: p for p in org["people"]}
    roles = {r["contact_id"]: r for r in org["role_assignments"]}
    units = {u["unit_id"]: u for u in org["units"]}
    by_unit = {}
    for pid, person in people.items():
        by_unit.setdefault(person["unit_id"], []).append(pid)
    def choose(unit_code, predicate):
        unit_ids = [u["unit_id"] for u in org["units"] if u["unit_code"] == unit_code]
        candidates = [pid for uid in unit_ids for pid in by_unit.get(uid, [])
                      if predicate(roles[pid]["role_code"])]
        if not candidates:
            raise ValueError(f"no eligible staff in {org['organization_id']} / {unit_code}")
        return sorted(candidates)[0]
    director = choose("headquarters", lambda role: role == "director")
    managers = {}
    for unit in org["units"]:
        code = unit["unit_code"]
        if code == "headquarters":
            continue
        managers[code] = choose(code, lambda role: role.endswith("_manager") or role == "head_of_sales")
    sales_initiator = choose("sales", lambda role: role in {
        "account_manager", "corporate_sales_manager", "business_development_specialist",
        "sales_specialist"
    })
    return {"people": people, "roles": roles, "units": units, "managers": managers,
            "director": director, "sales_initiator": sales_initiator}


def _deal_family_sequence(config, seed, org_index):
    plan = _family_plan(config)
    rows = [family for family in FAMILY_ORDER for _ in range(plan[family] // config["organizations"])]
    # Contract quotas are divisible by 20: each organization receives exactly
    # 20 routine, 10 conflict, 6 rejected and 4 multi-level episodes.
    if len(rows) != config["deals_per_organization"]:
        raise ValueError("per-organization family quota is not integral")
    random.Random(seed * 1009 + org_index * 9176).shuffle(rows)
    return rows


def _grant(org_id, person_id, scope, grant_id):
    return {
        "grant_id": grant_id, "organization_id": org_id, "contact_id": person_id,
        "scope": scope, "valid_from": "2026-01-01T00:00:00+00:00",
        "valid_until": None, "revoked_at": None,
        "source_ref": f"synthetic-policy:{org_id}:{scope}"
    }


def build(seed=None, config=None):
    cfg = _load_config(config)
    seed = cfg["seed"] if seed is None else seed
    if seed != cfg["seed"]:
        raise ValueError("canonical v4 QC must use the approved seed")
    if cfg.get("generation_authorized") is not False or cfg.get("bulk_generation_enabled") is not False:
        raise ValueError("canonical scenario engine is QC-only; generation flags must remain false")
    if cfg["organizations"] != 20 or cfg["deals_per_organization"] != 40:
        raise ValueError("this implementation is pinned to the approved 20 x 40 contract")
    if cfg["total_deals"] != cfg["organizations"] * cfg["deals_per_organization"]:
        raise ValueError("total deal count mismatch")
    plan = _family_plan(cfg)
    orgs = build_organizations(seed=seed, count=cfg["organizations"], config=cfg)
    rng = random.Random(seed)
    world_deals, events, observable_events, grants, truth = [], [], [], [], []
    missingness_candidates = []
    org_indexes = {o["organization_id"]: _staff_index(o) for o in orgs}

    for org_index, org in enumerate(orgs):
        oid = org["organization_id"]
        staff = org_indexes[oid]
        for scope, person_id in [("deal_approval", staff["director"])]:
            grants.append(_grant(oid, person_id, scope, f"{oid}:GRANT:{scope}:001"))
        for unit_code, person_id in sorted(staff["managers"].items()):
            grants.append(_grant(oid, person_id, f"unit_approval:{unit_code}",
                                 f"{oid}:GRANT:unit:{unit_code}:001"))

        family_sequence = _deal_family_sequence(cfg, seed, org_index)
        for deal_index, family in enumerate(family_sequence, 1):
            deal_id = f"{oid}-D{deal_index:04d}"
            deal = {"deal_id": deal_id, "organization_id": oid,
                    "organization_index": org_index + 1, "family": family,
                    "status": "open", "scenario_seed": seed}
            world_deals.append(deal)
            start = datetime(2026, 2, 1, tzinfo=timezone.utc) + timedelta(days=deal_index * 3 + org_index)
            previous = None
            local_events = []

            def emit(event_type, actor_id, target_id=None, *, scope="deal_approval",
                     context_note=None, decision_outcome=None, authority_grant_ref=None):
                nonlocal previous, start
                start += timedelta(hours=1 + rng.randrange(1, 8))
                event_id = f"{deal_id}-E{len(local_events) + 1:03d}"
                event = {
                    "event_id": event_id, "deal_id": deal_id, "organization_id": oid,
                    "event_type": event_type, "occurred_at": start.isoformat(),
                    "previous_event_id": previous, "actor_contact_id": actor_id,
                    "target_contact_id": target_id, "decision_scope": scope,
                    "context_note": context_note or f"{event_type} for {deal_id}",
                    "decision_outcome": decision_outcome,
                    "authority_grant_ref": authority_grant_ref,
                    "source_ref": f"SRC:{event_id}"
                }
                local_events.append(event)
                previous = event_id
                return event

            sales = staff["sales_initiator"]
            technical = staff["managers"]["technical"]
            finance = staff["managers"]["finance"]
            procurement = staff["managers"]["procurement"]
            director = staff["director"]

            emit("request_information", sales, procurement,
                 context_note="Initial business requirement and request for review")
            emit("delegate", procurement, technical,
                 scope="unit_approval:technical",
                 context_note="Technical assessment assigned")
            emit("complete_task", technical, procurement,
                 scope="unit_approval:technical",
                 context_note="Technical assessment completed")
            emit("review", procurement, technical,
                 context_note="Initial review of evidence and requirements")

            if family == "conflict_revision":
                emit("object", finance, sales,
                     context_note="Explicit objection: budget or commercial condition is not acceptable")
                emit("revise", sales, finance,
                     context_note="Revised proposal submitted in response to objection")
                emit("review", finance, sales,
                     context_note="Revised proposal reviewed after objection")
                emit("recommend", finance, director,
                     context_note="Recommendation after conflict resolution")
            elif family == "rejected":
                emit("recommend", technical, director,
                     context_note="Expert recommendation submitted for final review")
                emit("reject", director, None, decision_outcome="rejected",
                     authority_grant_ref=f"{oid}:GRANT:deal_approval:001")
            elif family == "multi_level_approval":
                emit("unit_approval", technical, director, scope="unit_approval:technical",
                     context_note="Technical unit approval recorded",
                     authority_grant_ref=f"{oid}:GRANT:unit:technical:001")
                emit("unit_approval", finance, director, scope="unit_approval:finance",
                     context_note="Finance unit approval recorded",
                     authority_grant_ref=f"{oid}:GRANT:unit:finance:001")
                emit("unit_approval", procurement, director, scope="unit_approval:procurement",
                     context_note="Procurement unit approval recorded",
                     authority_grant_ref=f"{oid}:GRANT:unit:procurement:001")
                emit("recommend", procurement, director,
                     context_note="Cross-functional recommendation submitted")
                emit("approve", director, None, decision_outcome="approved",
                     authority_grant_ref=f"{oid}:GRANT:deal_approval:001")
            else:
                emit("recommend", technical, director,
                     context_note="Routine expert recommendation submitted")
                emit("approve", director, None, decision_outcome="approved",
                     authority_grant_ref=f"{oid}:GRANT:deal_approval:001")

            if family == "conflict_revision":
                emit("approve", director, None, decision_outcome="approved",
                     authority_grant_ref=f"{oid}:GRANT:deal_approval:001")
            outcome = "rejected" if family == "rejected" else "approved"
            deal["status"] = outcome
            emit("close", sales, None, decision_outcome=outcome,
                 context_note=f"Deal episode closed with outcome {outcome}")
            events.extend(local_events)

    # Select exactly 10% of distinct deal episodes, deterministically and evenly
    # across organizations. The hidden truth is never altered by this masking.
    missingness = cfg["observable_missingness"]
    affected_per_org = missingness["affected_deal_count"] // cfg["organizations"]
    for org_index, org in enumerate(orgs):
        oid = org["organization_id"]
        deal_ids = sorted(d["deal_id"] for d in world_deals if d["organization_id"] == oid)
        ranked = sorted(deal_ids, key=lambda did: hashlib.sha256(
            f"{seed}|{oid}|{did}|observable-missingness".encode()).hexdigest())
        missingness_candidates.extend(ranked[:affected_per_org])
    affected = set(missingness_candidates)
    if len(affected) != missingness["affected_deal_count"]:
        raise ValueError("observable missingness quota is not exact")

    for event in events:
        observable = {k: v for k, v in event.items()
                      if k not in ("authority_grant_ref", "decision_outcome")}
        # The source event note embeds the hidden final outcome for close events.
        # Replace it before observable missingness is applied.
        if event["event_type"] == "close":
            observable["context_note"] = "Deal episode closed"
        masked = []
        if event["deal_id"] in affected:
            for field in ELIGIBLE_MISSING_FIELDS:
                if observable.get(field) is not None:
                    observable[field] = None
                    masked.append(field)
        observable["missing_fields"] = masked
        observable_events.append(observable)

        grant_refs = []
        if event["authority_grant_ref"]:
            match = next((g for g in grants if g["grant_id"] == event["authority_grant_ref"]), None)
            if match is None or match["contact_id"] != event["actor_contact_id"]:
                raise ValueError("decision references missing or mismatched authority grant")
            grant_refs.append(match["grant_id"])
        truth.append({
            **event,
            "initiator_contact_id": next(e["actor_contact_id"] for e in events
                if e["deal_id"] == event["deal_id"] and e["event_type"] == "request_information"),
            "document_author_contact_id": event["actor_contact_id"],
            "speaker_contact_id": None,
            "speaker_status": "unknown_no_turn_annotation",
            "executor_contact_id": event["actor_contact_id"] if event["event_type"] in ("complete_task", "revise") else None,
            "decision_maker_contact_id": event["actor_contact_id"] if event["event_type"] in ("approve", "reject", "unit_approval") else None,
            "authority_grant_refs": grant_refs,
            "observable_missingness_applied": event["deal_id"] in affected,
            "annotation_origin": "canonical_scenario_engine_v4"
        })

    return {
        "schema_version": SCHEMA_VERSION, "seed": seed, "synthetic": True,
        "generation_mode": "in_memory_qc_only",
        "organizations": orgs, "deals": world_deals, "events": events,
        "observable_events": observable_events, "authority_grants": grants,
        "ground_truth": {"visibility": "evaluation_only", "records": truth},
        "missingness": {"mode": "observable_only", "affected_deal_ids": sorted(affected),
                        "affected_deal_count": len(affected),
                        "masked_field_counts": dict(Counter(
                            field for row in observable_events for field in row["missing_fields"]))}
    }


def validate(dataset, config=None):
    cfg = _load_config(config)
    errors = []
    check = lambda ok, message: errors.append(message) if not ok else None
    deals = dataset["deals"]
    events = dataset["events"]
    obs = dataset["observable_events"]
    gold = dataset["ground_truth"]["records"]
    check(len(dataset["organizations"]) == 20, "organization count")
    check(len(deals) == 800, "deal count")
    check(len(events) == 6440, "event count")
    check(len({d["deal_id"] for d in deals}) == len(deals), "duplicate deal IDs")
    check(len(events) == len(obs) == len(gold), "event projection coverage")
    check(len({e["event_id"] for e in events}) == len(events), "duplicate event IDs")
    check(dataset["ground_truth"]["visibility"] == "evaluation_only", "ground truth visibility")
    check(dataset["generation_mode"] == "in_memory_qc_only", "generation mode")
    family_counts = Counter(d["family"] for d in deals)
    for family, expected in _family_plan(cfg).items():
        check(family_counts[family] == expected, f"exact family quota {family}")
    missing = dataset["missingness"]
    expected_missing = cfg["observable_missingness"]["affected_deal_count"]
    check(missing["affected_deal_count"] == expected_missing, "exact missingness deal quota")
    check(len(missing["affected_deal_ids"]) == expected_missing, "unique missingness deal IDs")
    deal_org_index = {d["deal_id"]: d["organization_id"] for d in deals}
    missing_by_org = Counter(deal_org_index[did] for did in missing["affected_deal_ids"] if did in deal_org_index)
    check(len(missing_by_org) == 20 and all(n == 4 for n in missing_by_org.values()), "missingness must affect four deals per organization")
    deal_ids = {d["deal_id"] for d in deals}
    check(set(missing["affected_deal_ids"]) <= deal_ids, "missingness orphan deal")
    org_ids = {o["organization_id"] for o in dataset["organizations"]}
    person_org = {p["contact_id"]: p["organization_id"]
                  for o in dataset["organizations"] for p in o["people"]}
    grants = {g["grant_id"]: g for g in dataset["authority_grants"]}
    obs_by_id = {e["event_id"]: e for e in obs}
    gold_by_id = {e["event_id"]: e for e in gold}
    deal_by_id = {d["deal_id"]: d for d in deals}
    by_deal = {}
    for event in events:
        by_deal.setdefault(event["deal_id"], []).append(event)
        check(event["organization_id"] in org_ids, "event organization")
        check(person_org.get(event["actor_contact_id"]) == event["organization_id"], "event actor org")
        target = event["target_contact_id"]
        check(target is None or person_org.get(target) == event["organization_id"], "event target org")
        check(event["event_type"] in EVENT_TYPES, "unknown event type")
        if event["event_type"] in ("approve", "reject", "unit_approval"):
            grant = grants.get(event["authority_grant_ref"])
            check(grant is not None, "decision grant missing")
            if grant:
                check(grant["contact_id"] == event["actor_contact_id"], "decision grant actor")
                check(grant["scope"] == event["decision_scope"], "decision grant scope")
                check(grant["valid_from"] <= event["occurred_at"], "decision grant validity")
    for deal_id, rows in by_deal.items():
        rows.sort(key=lambda e: e["occurred_at"])
        previous = None
        for event in rows:
            check(event["previous_event_id"] == previous, "broken event chain " + event["event_id"])
            previous = event["event_id"]
        check(rows[-1]["event_type"] == "close", "deal closure missing " + deal_id)
        final_decisions = [e for e in rows if e["event_type"] in ("approve", "reject")]
        check(len(final_decisions) == 1, "deal must have exactly one final decision " + deal_id)
        check(rows[-1]["decision_outcome"] == deal_by_id[deal_id]["status"], "deal outcome mismatch")
        if deal_by_id[deal_id]["family"] == "conflict_revision":
            types = [e["event_type"] for e in rows]
            check("object" in types and "revise" in types, "conflict revision evidence missing")
        if deal_by_id[deal_id]["family"] == "multi_level_approval":
            check(len({e["decision_scope"] for e in rows if e["event_type"] == "unit_approval"}) >= 3,
                  "multi-unit approvals missing")
    for event_id, observable in obs_by_id.items():
        truth = gold_by_id.get(event_id)
        check(truth is not None, "ground truth event missing")
        if truth is None:
            continue
        check(observable["event_id"] == event_id, "observable event ID")
        check(observable["deal_id"] == truth["deal_id"], "observable deal lineage")
        check(observable["organization_id"] == truth["organization_id"], "observable org lineage")
        if observable["deal_id"] not in set(missing["affected_deal_ids"]):
            check(observable["target_contact_id"] == truth["target_contact_id"], "unmasked target mismatch")
            expected_context = "Deal episode closed" if truth["event_type"] == "close" else truth["context_note"]
            check(observable["context_note"] == expected_context, "unmasked context mismatch")
            if truth["event_type"] == "close":
                check(not any(token in str(observable["context_note"]).lower() for token in ("approved", "rejected")),
                      "close outcome leaked through observable context")
        else:
            check(observable["missing_fields"] == [f for f in ELIGIBLE_MISSING_FIELDS
                  if truth.get(f) is not None], "missingness field mask")
        check(truth["speaker_contact_id"] is None, "speaker must remain unknown without turn labels")
    check(set(obs_by_id) == set(gold_by_id) == {e["event_id"] for e in events},
          "observable/ground truth event key parity")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "organizations": len(dataset["organizations"]), "deals": len(deals),
            "events": len(events), "ground_truth_records": len(gold),
            "scenario_family_counts": dict(family_counts),
            "missingness_deal_count": missing["affected_deal_count"],
            "authority_grants": len(grants), "generation_mode": dataset["generation_mode"]}


def audit(seed=None, config=None):
    cfg = _load_config(config)
    dataset = build(seed=seed, config=cfg)
    result = validate(dataset, cfg)
    result["seed"] = dataset["seed"]
    result["observable_missingness"] = dataset["missingness"]
    result["generation_authorized"] = cfg["generation_authorized"]
    result["bulk_generation_enabled"] = cfg["bulk_generation_enabled"]
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
