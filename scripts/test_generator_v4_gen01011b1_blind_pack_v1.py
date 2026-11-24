import json, tempfile, unittest
from pathlib import Path
from generator_v4_gen01011b1_blind_pack_v1 import main, OUT
class BlindPackTests(unittest.TestCase):
    def test_pack_build_and_blind_schema(self):
        main()
        p=json.loads((OUT/"blind"/"gen01011b1_blinded_pack.json").read_text(encoding="utf-8"))
        k=json.loads((OUT/"restricted"/"gen01011b1_restricted_answer_key.json").read_text(encoding="utf-8"))
        self.assertEqual(len(p["records"]),220)
        self.assertEqual(len(k["records"]),220)
        self.assertEqual({r["review_id"] for r in p["records"]},{r["review_id"] for r in k["records"]})
        for row in p["records"]:
            self.assertEqual(set(row),{"review_id","subject","body"})
        self.assertNotIn("ground_truth_event_type",json.dumps(p))
        self.assertTrue(p["records"] and all("channel" not in r and "record_format" not in r for r in p["records"]))
        self.assertEqual(p["sample_id"],"GEN01011B1-SEED-20261125")
if __name__=="__main__": unittest.main()
