import unittest

from generator_v4_scenario_engine_v1 import build
from generator_v4_communication_renderer_v1 import render_communications
from generator_v4_composite_bpmn_audit_v1 import CONFIG
from generator_v4_human_review_pack_v1 import EVENT_TYPES, build_review_pack


class HumanReviewPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = build(config=CONFIG)
        cls.communications = render_communications(
            cls.world["observable_events"], cls.world["organizations"], cls.world["seed"]
        )
        cls.pack, cls.key, cls.audit = build_review_pack(cls.communications, cls.world["seed"])

    def test_exact_sample_size_and_class_balance(self):
        self.assertEqual(self.audit["status"], "PASS")
        self.assertEqual(self.pack["sample_size"], 220)
        self.assertEqual(self.key["sample_size"], 220)
        self.assertEqual(len(self.audit["per_event_class"]), 11)
        self.assertTrue(all(v["sample"] == 20 for v in self.audit["per_event_class"].values()))

    def test_blinded_pack_does_not_expose_truth_or_identity(self):
        forbidden = {"event_type", "source_event_id", "source_ref", "organization_id",
                     "deal_id", "occurred_at", "author_contact_id", "participant_contact_ids"}
        for row in self.pack["records"]:
            self.assertFalse(forbidden.intersection(row))
            self.assertNotIn("ORG-", row["body"])
            self.assertNotIn("ORG-", row["subject"])

    def test_answer_key_is_separate_and_complete(self):
        self.assertTrue(self.key["restricted"])
        self.assertTrue(self.key["do_not_share_with_reviewers"])
        self.assertEqual({r["review_id"] for r in self.pack["records"]},
                         {r["review_id"] for r in self.key["records"]})
        self.assertEqual({r["ground_truth_event_type"] for r in self.key["records"]}, set(EVENT_TYPES))

    def test_deterministic_replay(self):
        pack2, key2, audit2 = build_review_pack(self.communications, self.world["seed"])
        self.assertEqual(self.pack, pack2)
        self.assertEqual(self.key, key2)
        self.assertEqual(self.audit, audit2)

    def test_review_fields_are_blank(self):
        for row in self.pack["records"]:
            self.assertIsNone(row["reviewer_1"]["primary_event_type"])
            self.assertIsNone(row["reviewer_2"]["primary_event_type"])
            self.assertIsNone(row["adjudication"]["primary_event_type"])


if __name__ == "__main__":
    unittest.main()
