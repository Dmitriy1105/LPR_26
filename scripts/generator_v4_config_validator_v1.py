"""Validate the approved Generator v4.0 configuration without generating data."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "generator_v4_0.json"

def validate_config(cfg):
    errors = []
    checks = {}
    def check(name, condition, message):
        checks[name] = bool(condition)
        if not condition:
            errors.append(message)

    check("schema_version", cfg.get("schema_version") == "1.0.0", "schema_version must be 1.0.0")
    check("contract_version", cfg.get("contract_version") == "1.0.0", "contract_version must be 1.0.0")
    check("generator_version", cfg.get("generator_version") == "4.0", "generator_version must be 4.0")
    check("generation_disabled", cfg.get("generation_authorized") is False and cfg.get("bulk_generation_enabled") is False,
          "generation must remain explicitly disabled")
    check("seed", type(cfg.get("seed")) is int and cfg.get("seed") == 42, "seed must be integer 42")
    orgs, per_org, total = cfg.get("organizations"), cfg.get("deals_per_organization"), cfg.get("total_deals")
    check("organization_count", type(orgs) is int and orgs == 20, "organizations must equal 20")
    check("deals_per_organization", type(per_org) is int and per_org == 40, "deals_per_organization must equal 40")
    check("total_deals", type(total) is int and total == 800 and orgs * per_org == total,
          "total_deals must equal organizations * deals_per_organization = 800")

    staff = cfg.get("employees_per_organization", {})
    check("variable_staff_range", isinstance(staff, dict) and staff.get("mode") == "variable"
          and staff.get("min") == 30 and staff.get("max") == 40 and staff.get("require_variation") is True,
          "employee configuration must be variable in inclusive range 30..40 with variation required")

    families = cfg.get("scenario_families", [])
    expected = {
        "routine_approval": (50, 400),
        "conflict_revision": (25, 200),
        "rejected": (15, 120),
        "multi_level_approval": (10, 80),
    }
    actual = {x.get("code"): x for x in families if isinstance(x, dict)}
    check("scenario_family_codes", set(actual) == set(expected) and len(families) == len(expected),
          "scenario families must contain exactly the four approved unique codes")
    if set(actual) == set(expected) and len(families) == len(expected):
        for code, (share, count) in expected.items():
            item = actual[code]
            check("scenario_" + code, item.get("share_percent") == share and item.get("exact_count") == count,
                  f"{code} must be exactly {share}% / {count} deals")
    check("scenario_shares_sum_100", sum(x.get("share_percent", 0) for x in families if isinstance(x, dict)) == 100,
          "scenario family shares must sum to 100")
    check("scenario_counts_sum_800", sum(x.get("exact_count", 0) for x in families if isinstance(x, dict)) == 800,
          "scenario family exact counts must sum to 800")
    conflict = actual.get("conflict_revision", {})
    check("conflict_requires_evidence", conflict.get("requires_explicit_conflict_evidence") is True,
          "conflict scenarios must require explicit conflict evidence")
    multi = actual.get("multi_level_approval", {})
    check("multilevel_requires_multiple_units", multi.get("requires_multiple_units") is True,
          "multi-level scenarios must require multiple organizational units")

    missing = cfg.get("observable_missingness", {})
    check("missingness_exact_80", isinstance(missing, dict)
          and missing.get("mode") == "observable_only"
          and missing.get("affected_deal_share_percent") == 10
          and missing.get("affected_deal_count") == 80
          and missing.get("selection_unit") == "distinct_deal_episode",
          "observable missingness must affect exactly 80 of 800 distinct deal episodes (10%)")
    check("missingness_preserves_gold", missing.get("preserve_hidden_ground_truth") is True,
          "observable missingness must preserve complete hidden Ground Truth")
    check("missingness_safe_fields", missing.get("mask_eligible_fields_only") is True
          and missing.get("never_mask_keys_or_lineage") is True,
          "missingness may mask eligible observable fields only, never keys or lineage")
    check("missingness_deterministic", missing.get("deterministic") is True,
          "missingness selection must be deterministic")

    required_units = {
        "headquarters", "sales", "finance", "technical", "procurement",
        "legal", "project_office", "security", "information_security"
    }
    check("organization_units", set(cfg.get("required_organization_units", [])) == required_units,
          "required organization units do not match the approved contract")
    gold = cfg.get("ground_truth", {})
    check("ground_truth_isolated", gold.get("completeness") == "complete_hidden_truth"
          and gold.get("separate_from_observable_input") is True
          and gold.get("accessible_to_nlp_inference") is False
          and gold.get("preserve_unknown_statuses") is True,
          "Ground Truth must remain complete, isolated from NLP input, and preserve unknown statuses")
    repro = cfg.get("reproducibility", {})
    check("reproducibility", repro.get("same_seed_same_logical_output") is True
          and repro.get("stable_entity_event_keys") is True and repro.get("manifest_sha256") is True,
          "reproducibility requirements are incomplete")
    legacy = cfg.get("legacy_compatibility", {})
    check("legacy_protection", legacy.get("preserve_v3_fixtures") is True
          and legacy.get("overwrite_legacy_fixtures") is False
          and legacy.get("require_reconciliation_before_migration") is True
          and set(legacy.get("unresolved_record_count_discrepancy", [])) == {677, 767},
          "legacy fixtures must be preserved and 677/767 discrepancy reconciled before migration")
    check("output_root", cfg.get("output_root") == "src/data/generator_v4_0/",
          "unexpected v4.0 output root")

    return {"status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors,
            "generation_authorized": cfg.get("generation_authorized"),
            "bulk_generation_enabled": cfg.get("bulk_generation_enabled")}

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONFIG
    cfg = json.loads(path.read_text(encoding="utf-8"))
    report = validate_config(cfg)
    report["config_path"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    report["checks_passed"] = sum(report["checks"].values())
    report["checks_total"] = len(report["checks"])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
