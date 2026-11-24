import copy
import json
import unittest
from pathlib import Path

from generator_v4_config_validator_v1 import validate_config

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / "config" / "generator_v4_0.json").read_text(encoding="utf-8"))

class GeneratorV4ConfigTests(unittest.TestCase):
    def test_approved_config_passes_without_generation(self):
        result = validate_config(copy.deepcopy(BASE))
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["generation_authorized"])
        self.assertFalse(result["bulk_generation_enabled"])
        self.assertTrue(all(result["checks"].values()))

    def test_rejects_wrong_seed(self):
        cfg = copy.deepcopy(BASE); cfg["seed"] = 43
        self.assertEqual(validate_config(cfg)["status"], "FAIL")

    def test_rejects_wrong_total(self):
        cfg = copy.deepcopy(BASE); cfg["total_deals"] = 799
        self.assertEqual(validate_config(cfg)["status"], "FAIL")

    def test_rejects_conflict_quota_drift(self):
        cfg = copy.deepcopy(BASE)
        cfg["scenario_families"][1]["exact_count"] = 199
        self.assertEqual(validate_config(cfg)["status"], "FAIL")

    def test_rejects_staff_range_drift(self):
        cfg = copy.deepcopy(BASE); cfg["employees_per_organization"]["min"] = 29
        self.assertEqual(validate_config(cfg)["status"], "FAIL")

    def test_rejects_missingness_cell_interpretation(self):
        cfg = copy.deepcopy(BASE); cfg["observable_missingness"]["selection_unit"] = "cells"
        self.assertEqual(validate_config(cfg)["status"], "FAIL")

    def test_rejects_ground_truth_leakage(self):
        cfg = copy.deepcopy(BASE); cfg["ground_truth"]["accessible_to_nlp_inference"] = True
        self.assertEqual(validate_config(cfg)["status"], "FAIL")

    def test_rejects_generation_enablement(self):
        cfg = copy.deepcopy(BASE); cfg["bulk_generation_enabled"] = True
        self.assertEqual(validate_config(cfg)["status"], "FAIL")

    def test_rejects_legacy_overwrite(self):
        cfg = copy.deepcopy(BASE); cfg["legacy_compatibility"]["overwrite_legacy_fixtures"] = True
        self.assertEqual(validate_config(cfg)["status"], "FAIL")

if __name__ == "__main__":
    unittest.main()
