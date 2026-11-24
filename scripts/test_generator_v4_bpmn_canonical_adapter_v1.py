import unittest
from generator_v4_bpmn_canonical_adapter_v1 import audit

class CanonicalBpmnAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit()
    def test_all_800_deals_execute_registered_bpmn_dmn(self):
        self.assertEqual(self.report["status"], "PASS")
        self.assertEqual(self.report["bpmn_dmn_executions"], 800)
        self.assertEqual(self.report["matched_outcomes"], 800)
    def test_event_journal_and_authority_reconcile(self):
        self.assertEqual(self.report["authority_checks"], 800)
        self.assertEqual(self.report["event_close_matches"], 800)
        self.assertEqual(self.report["errors"], [])
    def test_scenario_family_outcomes(self):
        self.assertEqual(self.report["outcome_distribution"], {"approve": 680, "reject": 120})
    def test_scope_and_generation_boundary_are_explicit(self):
        self.assertEqual(self.report["composite_call_activity_execution"],
                         "NOT_IMPLEMENTED_BY_RESTRICTED_EXECUTOR")
        self.assertFalse(self.report["generation_authorized"])
        self.assertFalse(self.report["bulk_generation_enabled"])

if __name__ == "__main__":
    unittest.main()
