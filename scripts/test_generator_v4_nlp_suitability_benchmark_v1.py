import unittest

from generator_v4_scenario_engine_v1 import build
from generator_v4_communication_renderer_v1 import render_communications
from generator_v4_composite_bpmn_audit_v1 import CONFIG
from generator_v4_nlp_suitability_benchmark_v1 import predict_event_type, run_benchmark


class NlpSuitabilityBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = build(config=CONFIG)
        cls.communications = render_communications(
            cls.world["observable_events"], cls.world["organizations"], cls.world["seed"]
        )
        cls.report = run_benchmark(cls.world, cls.communications)

    def test_canonical_benchmark_has_complete_coverage(self):
        self.assertEqual(self.report["status"], "PASS")
        self.assertEqual(self.report["communications"], 6440)
        self.assertEqual(self.report["unique_source_events"], 6440)

    def test_predictor_uses_body_text_and_abstains_on_unknown(self):
        self.assertEqual(predict_event_type("Текущая редакция вызывает возражение."), "object")
        self.assertEqual(predict_event_type("Нейтральный текст без признаков события."), "abstain")

    def test_organization_holdout_is_disjoint(self):
        dev = set(self.report["development_organizations"])
        held = set(self.report["held_out_organizations"])
        self.assertEqual(len(dev), 16)
        self.assertEqual(len(held), 4)
        self.assertFalse(dev & held)

    def test_binary_tasks_report_metrics(self):
        tasks = self.report["binary_event_tasks"]
        self.assertEqual(set(tasks), {"objection", "revision", "recommendation", "final_decision"})
        self.assertTrue(all(0 <= row["f1"] <= 1 for row in tasks.values()))

    def test_person_attribution_abstains_without_turn_evidence(self):
        attribution = self.report["person_attribution"]
        self.assertEqual(attribution["status"], "SAFE_ABSTENTION")
        self.assertEqual(attribution["predicted_person_ids"], 0)
        self.assertEqual(attribution["abstained_records"], 6440)


if __name__ == "__main__":
    unittest.main()
