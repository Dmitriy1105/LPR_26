import copy
import json
import unittest
from pathlib import Path

from generator_v4_config_validator_v1 import validate_config
from generator_v4_scenario_engine_v1 import build, validate

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "generator_v4_0.json").read_text(encoding="utf-8"))


class CanonicalScenarioEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = build(seed=42, config=copy.deepcopy(CONFIG))

    def test_full_approved_topology_in_memory_only(self):
        self.assertEqual(len(self.dataset["organizations"]), 20)
        self.assertEqual(len(self.dataset["deals"]), 800)
        self.assertEqual(self.dataset["generation_mode"], "in_memory_qc_only")
        self.assertFalse(CONFIG["generation_authorized"])
        self.assertFalse(CONFIG["bulk_generation_enabled"])

    def test_exact_family_quotas(self):
        self.assertEqual(validate(self.dataset)["scenario_family_counts"], {
            "routine_approval": 400, "conflict_revision": 200,
            "rejected": 120, "multi_level_approval": 80
        })

    def test_variable_headcount_and_real_organization_ids(self):
        counts = [len(o["people"]) for o in self.dataset["organizations"]]
        self.assertTrue(all(30 <= n <= 40 for n in counts))
        self.assertGreater(len(set(counts)), 1)
        person_ids = {p["contact_id"] for o in self.dataset["organizations"] for p in o["people"]}
        self.assertTrue(all(e["actor_contact_id"] in person_ids for e in self.dataset["events"]))

    def test_conflict_family_has_objection_and_revision(self):
        deals = {d["deal_id"]: d for d in self.dataset["deals"]}
        by_deal = {}
        for e in self.dataset["events"]:
            by_deal.setdefault(e["deal_id"], set()).add(e["event_type"])
        conflict_ids = [d["deal_id"] for d in deals.values() if d["family"] == "conflict_revision"]
        self.assertEqual(len(conflict_ids), 200)
        self.assertTrue(all({"object", "revise"} <= by_deal[x] for x in conflict_ids))

    def test_multilevel_scenarios_cross_three_units(self):
        for deal in [d for d in self.dataset["deals"] if d["family"] == "multi_level_approval"]:
            approvals = [e for e in self.dataset["events"]
                         if e["deal_id"] == deal["deal_id"] and e["event_type"] == "unit_approval"]
            self.assertGreaterEqual(len({e["decision_scope"] for e in approvals}), 3)

    def test_exact_observable_missingness_and_truth_preservation(self):
        miss = self.dataset["missingness"]
        self.assertEqual(miss["affected_deal_count"], 80)
        self.assertEqual(len(miss["affected_deal_ids"]), 80)
        gold = {r["event_id"]: r for r in self.dataset["ground_truth"]["records"]}
        observable = {r["event_id"]: r for r in self.dataset["observable_events"]}
        self.assertEqual(set(gold), set(observable))
        for event_id, truth in gold.items():
            if truth["deal_id"] in set(miss["affected_deal_ids"]):
                self.assertIsNotNone(truth["target_contact_id"])
                self.assertIsNone(observable[event_id]["target_contact_id"])
            else:
                self.assertEqual(observable[event_id]["target_contact_id"], truth["target_contact_id"])

    def test_ground_truth_is_separate_and_speaker_unknown(self):
        self.assertEqual(self.dataset["ground_truth"]["visibility"], "evaluation_only")
        self.assertTrue(all(r["speaker_contact_id"] is None for r in self.dataset["ground_truth"]["records"]))
        self.assertTrue(all("decision_outcome" not in r for r in self.dataset["observable_events"]))

    def test_authority_decisions_have_valid_grant_references(self):
        grants = {g["grant_id"]: g for g in self.dataset["authority_grants"]}
        decisions = [e for e in self.dataset["events"] if e["event_type"] in ("approve", "reject")]
        self.assertEqual(len(decisions), 800)
        for e in decisions:
            g = grants[e["authority_grant_ref"]]
            self.assertEqual(g["contact_id"], e["actor_contact_id"])
            self.assertEqual(g["scope"], "deal_approval")

    def test_event_lineage_and_unique_keys(self):
        ids = [e["event_id"] for e in self.dataset["events"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(e["source_ref"] == "SRC:" + e["event_id"] for e in self.dataset["events"]))

    def test_same_seed_reproducible(self):
        again = build(seed=42, config=copy.deepcopy(CONFIG))
        self.assertEqual(self.dataset, again)

    def test_rejects_enabled_generation(self):
        bad = copy.deepcopy(CONFIG)
        bad["generation_authorized"] = True
        with self.assertRaises(ValueError):
            build(config=bad)

    def test_rejects_config_drift(self):
        bad = copy.deepcopy(CONFIG)
        bad["scenario_families"][1]["exact_count"] = 199
        with self.assertRaises(ValueError):
            build(config=bad)

    def test_config_validator_still_passes(self):
        self.assertEqual(validate_config(copy.deepcopy(CONFIG))["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
