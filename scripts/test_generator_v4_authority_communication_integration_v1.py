import copy
import unittest

from generator_v4_scenario_engine_v1 import build
from generator_v4_authority_communication_integration_v1 import audit


class GeneratorV4AuthorityCommunicationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit()

    def test_all_decisions_pass_existing_temporal_authority_engine(self):
        self.assertEqual(self.result["status"], "PASS")
        self.assertEqual(self.result["authority_decisions_checked"], 1040)
        self.assertEqual(self.result["authority_errors"], [])

    def test_communication_projection_covers_every_event_without_fake_text(self):
        self.assertEqual(self.result["communication_projection_records"], 6440)
        self.assertTrue(self.result["communication_event_coverage"])
        self.assertEqual(self.result["communication_texts_rendered"], 0)

    def test_legacy_bpmn_boundary_is_explicit(self):
        self.assertEqual(self.result["bpmn_execution"], "BLOCKED_LEGACY_RUNTIME_USES_DEMO_ACTORS")

    def test_generation_remains_disabled(self):
        self.assertFalse(self.result["generation_authorized"])
        self.assertFalse(self.result["bulk_generation_enabled"])


if __name__ == "__main__":
    unittest.main()
