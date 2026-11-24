import copy
import json
import unittest
from pathlib import Path

from generator_v4_organization_adapter_v1 import build, validate

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "generator_v4_0.json").read_text(encoding="utf-8"))


class GeneratorV4OrganizationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.orgs = build(seed=42, count=20, config=copy.deepcopy(CONFIG))

    def test_builds_twenty_organizations(self):
        self.assertEqual(len(self.orgs), 20)
        self.assertEqual(len({o["organization_id"] for o in self.orgs}), 20)

    def test_employee_counts_are_variable_and_bounded(self):
        counts = [len(o["people"]) for o in self.orgs]
        self.assertTrue(all(30 <= n <= 40 for n in counts))
        self.assertGreater(len(set(counts)), 1)
        self.assertEqual(counts, [30 + ((42 + i * 7) % 11) for i in range(20)])

    def test_nine_required_units_and_one_headquarters_root(self):
        required = set(CONFIG["required_organization_units"])
        for org in self.orgs:
            self.assertEqual({u["unit_code"] for u in org["units"]}, required)
            roots = [u for u in org["units"] if u["parent_unit_id"] is None]
            self.assertEqual(len(roots), 1)
            self.assertEqual(roots[0]["unit_code"], "headquarters")

    def test_every_person_has_one_role_assignment(self):
        for org in self.orgs:
            self.assertEqual(len(org["people"]), len(org["role_assignments"]))
            self.assertEqual({p["contact_id"] for p in org["people"]},
                             {r["contact_id"] for r in org["role_assignments"]})

    def test_manager_and_unit_references_are_valid(self):
        for org in self.orgs:
            pids = {p["contact_id"] for p in org["people"]}
            uids = {u["unit_id"] for u in org["units"]}
            self.assertTrue(all(p["unit_id"] in uids for p in org["people"]))
            self.assertTrue(all(p["manager_contact_id"] is None or
                                p["manager_contact_id"] in pids for p in org["people"]))

    def test_deterministic_and_seed_sensitive(self):
        again = build(seed=42, count=20, config=copy.deepcopy(CONFIG))
        other_config = copy.deepcopy(CONFIG)
        other_config["seed"] = 43
        with self.assertRaises(ValueError):
            build(seed=43, count=20, config=other_config)
        self.assertEqual(self.orgs, again)

    def test_rejects_authorized_generation_flags(self):
        bad = copy.deepcopy(CONFIG)
        bad["bulk_generation_enabled"] = True
        with self.assertRaises(ValueError):
            build(seed=42, count=20, config=bad)

    def test_rejects_bad_headcount(self):
        bad = copy.deepcopy(self.orgs)
        bad[0]["people"] = bad[0]["people"][:-1]
        with self.assertRaises(ValueError):
            validate(bad)

    def test_rejects_dangling_manager(self):
        bad = copy.deepcopy(self.orgs)
        bad[0]["people"][1]["manager_contact_id"] = "NO-SUCH-PERSON"
        with self.assertRaises(ValueError):
            validate(bad)

    def test_rejects_cross_organization_reference(self):
        bad = copy.deepcopy(self.orgs)
        bad[0]["people"][1]["organization_id"] = bad[1]["organization_id"]
        with self.assertRaises(ValueError):
            validate(bad)

    def test_rejects_role_assignment_mismatch(self):
        bad = copy.deepcopy(self.orgs)
        bad[0]["role_assignments"][0]["unit_id"] = "NO-SUCH-UNIT"
        with self.assertRaises(ValueError):
            validate(bad)


if __name__ == "__main__":
    unittest.main()
