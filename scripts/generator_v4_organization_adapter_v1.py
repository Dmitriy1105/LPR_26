"""Canonical v4 organization adapter; builds an in-memory QC fixture only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from organization_engine_v1 import generate as generate_legacy, DEPARTMENTS
from roles_competencies_v1 import build as build_roles, validate as validate_roles

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "generator_v4_0.json"
VALID_FROM = "2026-01-01"
VALID_TO = None


def _target_headcount(seed: int, index: int, minimum: int, maximum: int) -> int:
    """Deterministic heterogeneous headcount, inclusive of configured bounds."""
    return minimum + ((seed + index * 7) % (maximum - minimum + 1))


def _normalize_staffing(org: dict, target: int) -> None:
    people = org["people"]
    units = {u["id"]: u for u in org["units"]}
    manager_by_unit = {
        p["unit"]: p["id"] for p in people
        if p["role"] != "director" and p["manager"] == org["id"] + ":P1"
    }
    specialist_roles = {
        "sales": ("corporate_sales_manager", "account_manager",
                  "business_development_specialist", "sales_specialist")
    }

    # Keep at least one specialist in every department. Managers and director
    # are structural anchors and are never removed by headcount normalization.
    specialists = [
        p for p in people
        if p["role"] != "director"
        and p["manager"] != org["id"] + ":P1"
    ]
    while len(people) > target:
        counts = {}
        for p in specialists:
            counts[p["unit"]] = counts.get(p["unit"], 0) + 1
        removable = [
            p for p in specialists
            if counts.get(p["unit"], 0) > 1
        ]
        if not removable:
            raise ValueError("cannot reach target headcount without removing department coverage")
        # Stable tie-breaking, independent of hash randomization.
        removable.sort(key=lambda p: (-(counts[p["unit"]]), p["unit"], p["id"]))
        victim = removable[0]
        people.remove(victim)
        specialists.remove(victim)

    counters = {u: 0 for u in manager_by_unit}
    department_order = sorted(manager_by_unit)
    cursor = 0
    while len(people) < target:
        unit_id = department_order[cursor % len(department_order)]
        cursor += 1
        counters[unit_id] += 1
        department = units[unit_id]["department"]
        manager_id = manager_by_unit[unit_id]
        existing = [p for p in people if p["unit"] == unit_id and p["manager"] == manager_id]
        serial = 1
        existing_ids = {p["id"] for p in people}
        while f"{manager_id}.V4.{serial}" in existing_ids:
            serial += 1
        if department == "sales":
            roles = specialist_roles["sales"]
            role = roles[(len(existing) + counters[unit_id] - 1) % len(roles)]
        else:
            role = department + "_specialist"
        person = {
            "id": f"{manager_id}.V4.{serial}",
            "unit": unit_id,
            "manager": manager_id,
            "role": role,
        }
        people.append(person)
        specialists.append(person)


def build(seed: int = 42, count: int = 20, config: dict | None = None) -> list[dict]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if type(count) is not int or count < 1:
        raise ValueError("organization count must be a positive integer")
    if config is None:
        config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    if config.get("generation_authorized") is not False or config.get("bulk_generation_enabled") is not False:
        raise ValueError("GEN-010.2 adapter is QC-only; generation flags must remain false")
    if count != config.get("organizations") or seed != config.get("seed"):
        raise ValueError("QC build must use the approved organization count and seed")
    staff = config.get("employees_per_organization", {})
    minimum, maximum = staff.get("min"), staff.get("max")
    if not (type(minimum) is int and type(maximum) is int and 1 <= minimum <= maximum):
        raise ValueError("invalid employee bounds")
    required_units = set(config.get("required_organization_units", []))
    if required_units != {"headquarters", *DEPARTMENTS}:
        raise ValueError("configuration unit set does not match Organization Engine")

    legacy_orgs = generate_legacy(seed=seed, count=count)
    result = []
    for index, legacy in enumerate(legacy_orgs):
        target = _target_headcount(seed, index, minimum, maximum)
        _normalize_staffing(legacy, target)
        # The existing engine remains the source of stable IDs and validated
        # reporting structure; this adapter adds the canonical v4 field names.
        role_rows = build_roles(legacy)
        validate_roles(legacy, role_rows)
        unit_rows = [
            {
                "unit_id": u["id"],
                "legacy_unit_id": u["id"],
                "organization_id": legacy["id"],
                "parent_unit_id": u["parent"],
                "unit_code": u["department"],
                "valid_from": VALID_FROM,
                "valid_to": VALID_TO,
            }
            for u in legacy["units"]
        ]
        people_rows = [
            {
                "contact_id": p["id"],
                "legacy_person_id": p["id"],
                "organization_id": legacy["id"],
                "unit_id": p["unit"],
                "manager_contact_id": p["manager"],
                "employment_status": "active",
                "valid_from": VALID_FROM,
                "valid_to": VALID_TO,
            }
            for p in legacy["people"]
        ]
        assignments = [
            {
                "role_assignment_id": row["person_id"] + ":ROLE:001",
                "contact_id": row["person_id"],
                "role_code": row["position"],
                "unit_id": row["department"],
                "valid_from": VALID_FROM,
                "valid_to": VALID_TO,
                "source_ref": None,
                "level": row["level"],
                "competencies": list(row["competencies"]),
                "authority_refs": list(row["authority_refs"]),
                "influence_evidence": list(row["influence_evidence"]),
            }
            for row in role_rows
        ]
        # Resolve role assignment unit IDs to canonical unit IDs.
        dept_to_unit = {u["unit_code"]: u["unit_id"] for u in unit_rows}
        for assignment in assignments:
            assignment["unit_id"] = dept_to_unit[assignment["unit_id"]]
        canonical = {
            "organization_id": legacy["id"],
            "legacy_organization_id": legacy["id"],
            "organization_index": index + 1,
            "target_employee_count": target,
            "units": unit_rows,
            "people": people_rows,
            "role_assignments": assignments,
        }
        validate([canonical], minimum, maximum, required_units)
        result.append(canonical)
    if len({o["target_employee_count"] for o in result}) < 2:
        raise ValueError("employee counts must vary across organizations")
    return result


def validate(orgs: list[dict], minimum: int = 30, maximum: int = 40,
             required_units: set[str] | None = None) -> bool:
    if required_units is None:
        required_units = {"headquarters", *DEPARTMENTS}
    if not isinstance(orgs, list) or not orgs:
        raise ValueError("organizations must be a non-empty list")
    seen_orgs = set()
    for org in orgs:
        oid = org["organization_id"]
        if oid in seen_orgs:
            raise ValueError("duplicate organization_id")
        seen_orgs.add(oid)
        units = org["units"]
        people = org["people"]
        roles = org["role_assignments"]
        unit_ids = [u["unit_id"] for u in units]
        person_ids = [p["contact_id"] for p in people]
        role_ids = [r["role_assignment_id"] for r in roles]
        if len(unit_ids) != len(set(unit_ids)) or len(person_ids) != len(set(person_ids)):
            raise ValueError("duplicate unit or person identifier")
        if len(role_ids) != len(set(role_ids)):
            raise ValueError("duplicate role assignment identifier")
        if not minimum <= len(people) <= maximum:
            raise ValueError("employee count outside configured range")
        if len(people) != len(roles):
            raise ValueError("role assignment coverage mismatch")
        unit_by_id = {u["unit_id"]: u for u in units}
        person_by_id = {p["contact_id"]: p for p in people}
        role_by_person = {r["contact_id"]: r for r in roles}
        if len(role_by_person) != len(roles) or set(role_by_person) != set(person_by_id):
            raise ValueError("role assignment person coverage mismatch")
        if {u["unit_code"] for u in units} != required_units:
            raise ValueError("required organization unit coverage mismatch")
        roots = [u for u in units if u["parent_unit_id"] is None]
        if len(roots) != 1 or roots[0]["unit_code"] != "headquarters":
            raise ValueError("organization must have exactly one headquarters root")
        for unit in units:
            if unit["organization_id"] != oid:
                raise ValueError("cross-organization unit reference")
            parent = unit["parent_unit_id"]
            if parent is not None and parent not in unit_by_id:
                raise ValueError("unknown parent unit")
            seen = set()
            current = unit["unit_id"]
            while current is not None:
                if current in seen or current not in unit_by_id:
                    raise ValueError("unit hierarchy cycle or dangling reference")
                seen.add(current)
                current = unit_by_id[current]["parent_unit_id"]
        for person in people:
            if person["organization_id"] != oid:
                raise ValueError("cross-organization person reference")
            if person["unit_id"] not in unit_by_id:
                raise ValueError("person references unknown unit")
            manager = person["manager_contact_id"]
            if manager is not None and manager not in person_by_id:
                raise ValueError("person references unknown manager")
            seen = set()
            current = person["contact_id"]
            while current is not None:
                if current in seen or current not in person_by_id:
                    raise ValueError("person hierarchy cycle or dangling reference")
                seen.add(current)
                current = person_by_id[current]["manager_contact_id"]
        for assignment in roles:
            person = person_by_id[assignment["contact_id"]]
            if assignment["unit_id"] != person["unit_id"]:
                raise ValueError("role assignment unit mismatch")
            if assignment["valid_from"] > (assignment["valid_to"] or "9999-12-31"):
                raise ValueError("invalid role assignment period")
            if assignment["authority_refs"] or assignment["influence_evidence"]:
                raise ValueError("authority/influence must not be inferred by organization adapter")
    return True


def main():
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    orgs = build(seed=config["seed"], count=config["organizations"], config=config)
    report = {
        "status": "PASS",
        "scope": "in-memory organization integration QC only; no deal or communication generation",
        "seed": config["seed"],
        "organizations": len(orgs),
        "employee_counts": {o["organization_id"]: len(o["people"]) for o in orgs},
        "total_employees": sum(len(o["people"]) for o in orgs),
        "unit_count_per_organization": sorted({len(o["units"]) for o in orgs}),
        "role_assignment_count": sum(len(o["role_assignments"]) for o in orgs),
        "generation_authorized": config["generation_authorized"],
        "bulk_generation_enabled": config["bulk_generation_enabled"],
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
