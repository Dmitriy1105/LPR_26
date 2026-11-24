import unittest
from generator_v4_annotation_ground_truth_audit_v1 import evaluate, CLASSES


def fixture():
    labels=[]
    for c in CLASSES:
        labels.extend([c]*20)
    annotations={"records":[{"review_id":f"HR-{i:03d}","reviewer_llm_v2":{
        "primary_event_type":label,"event_clarity_1_to_5":4,"naturalness_1_to_5":3,
        "factual_support_1_to_5":4,"unsupported_claims":[]}}
        for i,label in enumerate(labels,1)]}
    key={"records":[{"review_id":f"HR-{i:03d}","ground_truth_event_type":label,
        "channel":"email"} for i,label in enumerate(labels,1)]}
    return annotations,key


class AnnotationGroundTruthAuditTests(unittest.TestCase):
    def test_perfect_fixture(self):
        a,k=fixture()
        r=evaluate(a,k)
        self.assertEqual(r["n"],220)
        self.assertEqual(r["primary_metrics"]["accuracy"],1.0)
        self.assertEqual(r["primary_metrics"]["macro_f1_11_gt_classes"],1.0)
        self.assertFalse(r["annotation_provenance"]["is_true_llm_inference"])

    def test_unclear_counts_as_miss(self):
        a,k=fixture()
        a["records"][0]["reviewer_llm_v2"]["primary_event_type"]="unclear"
        r=evaluate(a,k)
        self.assertEqual(r["primary_metrics"]["accuracy"],219/220)
        self.assertEqual(r["per_class"][CLASSES[0]]["recall"],0.95)

    def test_incomplete_ids_rejected(self):
        a,k=fixture()
        a["records"].pop()
        with self.assertRaises(ValueError):
            evaluate(a,k)

    def test_duplicate_ids_rejected(self):
        a,k=fixture()
        a["records"][1]["review_id"]=a["records"][0]["review_id"]
        with self.assertRaises(ValueError):
            evaluate(a,k)


if __name__=="__main__":
    unittest.main()
