import copy
import unittest

from generator_v4_scenario_engine_v1 import build
from generator_v4_communication_renderer_v1 import render_communications
from generator_v4_communication_semantic_audit_v1 import audit_rendered_communications
from generator_v4_composite_bpmn_audit_v1 import CONFIG


class CommunicationSemanticAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = build(config=CONFIG)
        cls.communications = render_communications(
            cls.world["observable_events"], cls.world["organizations"], cls.world["seed"]
        )

    def test_canonical_semantic_and_attribution_audit_passes(self):
        report = audit_rendered_communications(self.world, self.communications)
        self.assertEqual(report["status"], "PASS", report["errors"][:20])
        self.assertEqual(report["communications"], 6440)
        self.assertEqual(report["unique_sources"], 6440)
        self.assertEqual(report["checks"]["executor_event_type_reconciliation"], 1000)
        self.assertEqual(report["checks"]["decision_actor_authority_reconciliation"], 1040)
        self.assertTrue(all(row["confirming_source_ref"] == row["source_ref"] for row in self.communications))
        self.assertTrue(all((row["action_executor_contact_id"] == row["author_contact_id"])
                            if row["event_type"] in ("complete_task", "revise")
                            else row["action_executor_contact_id"] is None for row in self.communications))
        self.assertTrue(all((row["decision_actor_contact_id"] == row["author_contact_id"])
                            if row["event_type"] in ("approve", "reject", "unit_approval")
                            else row["decision_actor_contact_id"] is None for row in self.communications))

    def test_wrong_author_is_detected(self):
        rows = copy.deepcopy(self.communications)
        rows[0]["author_contact_id"] = "UNKNOWN"
        report = audit_rendered_communications(self.world, rows)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("author" in error for error in report["errors"]))

    def test_wrong_channel_is_detected(self):
        rows = copy.deepcopy(self.communications)
        rows[0]["channel"] = "meeting" if rows[0]["channel"] != "meeting" else "email"
        report = audit_rendered_communications(self.world, rows)
        self.assertTrue(any("channel mapping mismatch" in error for error in report["errors"]))

    def test_wrong_role_label_is_detected(self):
        rows = copy.deepcopy(self.communications)
        rows[0]["author_role_label"] = "неверная роль"
        report = audit_rendered_communications(self.world, rows)
        self.assertTrue(any("author role label mismatch" in error for error in report["errors"]))

    def test_altered_context_is_detected(self):
        rows = copy.deepcopy(self.communications)
        index = next(i for i, row in enumerate(rows) if row["context_note_included"])
        rows[index]["body"] = rows[index]["body"].replace(
            self.world["observable_events"][index]["context_note"], "unverified claim"
        )
        report = audit_rendered_communications(self.world, rows)
        self.assertTrue(any("observable context omitted or altered" in error for error in report["errors"]))

    def test_close_outcome_leak_is_detected(self):
        rows = copy.deepcopy(self.communications)
        index = next(i for i, row in enumerate(rows) if row["event_type"] == "close")
        rows[index]["body"] += " Итог сделки approved."
        report = audit_rendered_communications(self.world, rows)
        self.assertTrue(any("closure communication exposes final outcome" in error for error in report["errors"]))

    def test_unit_approval_cannot_be_promoted_to_final_decision(self):
        rows = copy.deepcopy(self.communications)
        index = next(i for i, row in enumerate(rows) if row["event_type"] == "unit_approval")
        rows[index]["body"] += " Это итоговое одобрение сделки."
        report = audit_rendered_communications(self.world, rows)
        self.assertTrue(any("unit approval inflated" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
