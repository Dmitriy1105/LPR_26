import re
import unittest
from collections import Counter, defaultdict

from generator_v4_scenario_engine_v1 import build
from generator_v4_communication_renderer_v1 import (
    render_communications, validate_rendered_communications
)
from generator_v4_composite_bpmn_audit_v1 import CONFIG


class CanonicalCommunicationRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = build(config=CONFIG)
        cls.first = render_communications(cls.world["observable_events"], cls.world["organizations"], cls.world["seed"])
        cls.replay = render_communications(cls.world["observable_events"], cls.world["organizations"], cls.world["seed"])
        cls.validation = validate_rendered_communications(cls.world["observable_events"], cls.first)

    def test_every_observable_event_has_exactly_one_communication(self):
        self.assertEqual(self.validation["status"], "PASS")
        self.assertEqual(self.validation["communications"], 6440)
        self.assertEqual(self.validation["unique_source_events"], 6440)

    def test_same_seed_is_deterministic(self):
        self.assertEqual(self.first, self.replay)

    def test_channel_distribution_and_event_type_mapping(self):
        counts = Counter(row["channel"] for row in self.first)
        self.assertEqual(counts, {"email": 2600, "call": 1000, "meeting": 2840})
        expected = {"email": 4, "call": 2, "meeting": 1}
        self.assertTrue(all(row["type_id"] == expected[row["channel"]] for row in self.first))

    def test_body_diversity_minimum_per_event_type(self):
        grouped = defaultdict(list)
        for row in self.first:
            value = row["body"].lower()
            value = re.sub(r"org-\d+-d\d+-e\d+|org-\d+-d\d+|comm:org-\d+-d\d+-e\d+", " ", value)
            value = re.sub(r"\b\d+\b", " ", value)
            value = re.sub(r"[^\wа-яё]+", " ", value, flags=re.IGNORECASE).strip()
            grouped[row["event_type"]].append(value)
        ratios = {kind: len(set(texts)) / len(texts) for kind, texts in grouped.items()}
        self.assertEqual(len(ratios), 11)
        self.assertTrue(all(ratio >= 0.55 for ratio in ratios.values()), ratios)

    def test_attribution_and_participant_lineage(self):
        self.assertTrue(all(row["author_contact_id"] for row in self.first))
        self.assertTrue(all(row["participant_contact_ids"] for row in self.first))
        self.assertTrue(all(row["source_ref"] and row["source_event_id"] for row in self.first))

    def test_unknown_speaker_is_not_fabricated(self):
        self.assertTrue(all(row["speaker_contact_id"] is None for row in self.first))
        self.assertTrue(all(row["speaker_status"] == "unknown_no_turn_annotation" for row in self.first))

    def test_observable_missingness_is_preserved(self):
        missing = [row for row in self.first if row["missing_fields"]]
        self.assertGreater(len(missing), 0)
        self.assertTrue(all(not row["context_note_included"] for row in missing))

    def test_internal_scenario_labels_are_not_rendered_into_body(self):
        for row in self.first:
            self.assertNotIn("Контекст события:", row["body"])
            self.assertNotIn("Область согласования:", row["body"])
            self.assertNotIn("unit_approval:", row["body"].lower())

    def test_ground_truth_fields_are_not_exposed(self):
        forbidden = {"authority_grant_ref", "authority_grant_refs", "decision_outcome",
                     "ground_truth", "decision_maker_contact_id", "executor_contact_id"}
        self.assertTrue(all(not forbidden.intersection(row) for row in self.first))
        close = [row for row in self.first if row["event_type"] == "close"]
        self.assertTrue(all(not any(token in row["body"].lower() for token in
                            ("одобр", "отклон", "approved", "rejected")) for row in close))

    def test_all_event_types_are_rendered(self):
        event_types = {row["event_type"] for row in self.first}
        self.assertEqual(len(event_types), 11)


if __name__ == "__main__":
    unittest.main()
