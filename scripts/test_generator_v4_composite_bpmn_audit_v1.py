import unittest
from generator_v4_composite_bpmn_audit_v1 import audit

class CompositeBpmnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=audit()
    def test_all_canonical_deals_execute_composite_process(self):
        self.assertEqual(self.report["status"],"PASS")
        self.assertEqual(self.report["composite_executions"],800)
    def test_unit_approval_authority_is_reconciled(self):
        self.assertEqual(self.report["unit_approval_authority_checks"],240)
        self.assertEqual(self.report["unit_authority_errors"],0)
    def test_nested_call_activities_execute(self):
        self.assertTrue(self.report["nested_call_activity_execution"])
        self.assertEqual(self.report["process_id"],"corporate_multilevel_universal")
    def test_exact_conflict_revision_uses_revision_path(self):
        conflict=[r for r in self.report["results"] if r["family"]=="conflict_revision"]
        self.assertEqual(len(conflict),200)
        self.assertTrue(all(r["deal_outcome"]=="approve" for r in conflict))
    def test_generation_remains_disabled(self):
        self.assertFalse(self.report["generation_authorized"])
        self.assertFalse(self.report["bulk_generation_enabled"])
    def test_financial_evidence_limitation_is_visible(self):
        self.assertEqual(self.report["financial_policy_evidence"],
                         "SYNTHETIC_INPUTS_ONLY_NO_CANONICAL_BUDGET_BANDS")

if __name__=="__main__":
    unittest.main()
