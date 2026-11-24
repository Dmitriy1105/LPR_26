import unittest

from generator_v4_human_review_evaluator_v1 import evaluate, _kappa


def rows(labels, field="primary_event_type"):
    return [{"review_id": f"HR-{i:03d}", field: label,
             "event_clarity_1_to_5": 4, "naturalness_1_to_5": 4,
             "factual_support_1_to_5": 5, "unsupported_claims": []}
            for i, label in enumerate(labels, 1)]


class HumanReviewEvaluatorTests(unittest.TestCase):
    def test_perfect_agreement_kappa(self):
        result = _kappa(["approve", "reject", "approve"], ["approve", "reject", "approve"])
        self.assertEqual(result["raw_agreement"], 1.0)
        self.assertEqual(result["cohen_kappa"], 1.0)

    def test_no_agreement_with_nonzero_expected(self):
        result = _kappa(["approve", "reject"], ["reject", "approve"])
        self.assertEqual(result["raw_agreement"], 0.0)
        self.assertEqual(result["cohen_kappa"], -1.0)

    def test_full_evaluation_requires_220_complete_rows(self):
        labels = ["request_information"] * 20 + ["delegate"] * 20 + ["complete_task"] * 20 + ["review"] * 20 + ["recommend"] * 20 + ["object"] * 20 + ["revise"] * 20 + ["unit_approval"] * 20 + ["approve"] * 20 + ["reject"] * 20 + ["close"] * 20
        ids = [f"HR-{i:03d}" for i in range(1, 221)]
        reviewer1 = {"records": [dict(row, review_id=rid) for row, rid in zip(rows(labels), ids)]}
        reviewer2 = {"records": [dict(row, review_id=rid) for row, rid in zip(rows(labels), ids)]}
        adjudicated = {"records": [dict(row, review_id=rid, reason="reviewed") for row, rid in zip(rows(labels), ids)]}
        key = {"records": [{"review_id": rid, "ground_truth_event_type": label,
                            "channel": "email"} for rid, label in zip(ids, labels)]}
        report = evaluate(reviewer1, reviewer2, adjudicated, key)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["reviewer_agreement"]["cohen_kappa"], 1.0)
        self.assertEqual(report["adjudication_vs_ground_truth"]["accuracy"], 1.0)

    def test_missing_label_rejected(self):
        labels = ["approve"] * 220
        ids = [f"HR-{i:03d}" for i in range(1, 221)]
        r1 = {"records": [dict(row, review_id=rid) for row, rid in zip(rows(labels), ids)]}
        r2 = {"records": [dict(row, review_id=rid) for row, rid in zip(rows(labels), ids)]}
        adj = {"records": [dict(row, review_id=rid, reason="ok") for row, rid in zip(rows(labels), ids)]}
        r1["records"][0]["primary_event_type"] = None
        key = {"records": [{"review_id": rid, "ground_truth_event_type": label, "channel": "email"} for rid, label in zip(ids, labels)]}
        with self.assertRaises(ValueError):
            evaluate(r1, r2, adj, key)


if __name__ == "__main__":
    unittest.main()
