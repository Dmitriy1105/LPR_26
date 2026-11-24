import copy
import json
import unittest
from pathlib import Path

from generator_v4_organization_adapter_v1 import build as build_organizations
from generator_v4_authority_adapter_v1 import evaluate, validate_bundle

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "generator_v4_0.json").read_text(encoding="utf-8"))


def bundle(org):
    people = sorted(p["contact_id"] for p in org["people"])
    actor, delegatee = people[0], people[1]
    oid = org["organization_id"]
    grants = [
        {"grant_id": oid+":G1", "org_id": oid, "person_id": actor,
         "action": "contract", "permission": "final_decision",
         "valid_from": "2026-01-01", "valid_until": "2027-01-01",
         "max_amount": 100000, "source_ref": "synthetic-policy:board-approval"},
        {"grant_id": oid+":G2", "org_id": oid, "person_id": actor,
         "action": "contract", "permission": "delegate",
         "valid_from": "2026-01-01", "valid_until": "2027-01-01",
         "max_amount": 50000, "source_ref": "synthetic-policy:delegation-right"},
    ]
    bands = [
        {"band_id": oid+":B1", "org_id": oid, "person_id": actor,
         "action": "contract", "permission": "approve", "currency": "SGD",
         "min_amount": 0, "max_amount": 100000,
         "valid_from": "2026-01-01", "valid_until": "2027-01-01",
         "source_ref": "synthetic-policy:finance-band"}
    ]
    delegations = [
        {"delegation_id": oid+":D1", "org_id": oid,
         "delegator_id": actor, "delegatee_id": delegatee,
         "source_grant_id": oid+":G2", "action": "contract",
         "permission": "approve", "valid_from": "2026-02-01",
         "valid_until": "2026-12-01", "max_amount": 20000,
         "source_ref": "synthetic-policy:delegation-order",
         "redelegation": False}
    ]
    return actor, delegatee, grants, bands, delegations


class GeneratorV4AuthorityAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orgs = build_organizations(seed=42, count=20, config=copy.deepcopy(CONFIG))

    def test_authority_bundles_validate_for_all_twenty_organizations(self):
        for org in self.orgs:
            actor, delegatee, grants, bands, delegations = bundle(org)
            self.assertTrue(validate_bundle(org, grants, bands, delegations))

    def test_temporal_final_decision_grant(self):
        org = self.orgs[0]; actor, _, g, b, d = bundle(org)
        result = evaluate(org, g, b, d, actor_id=actor, action="contract",
                          permission="final_decision", as_of="2026-06-01")
        self.assertTrue(result["authorized"])
        self.assertEqual(result["authority_source"], g[0]["grant_id"])

    def test_financial_approval_band_and_currency(self):
        org = self.orgs[0]; actor, _, g, b, d = bundle(org)
        result = evaluate(org, g, b, d, actor_id=actor, action="contract",
                          permission="approve", as_of="2026-06-01",
                          amount=100000, currency="SGD")
        self.assertTrue(result["authorized"])
        wrong_currency = evaluate(org, g, b, d, actor_id=actor, action="contract",
                                  permission="approve", as_of="2026-06-01",
                                  amount=100, currency="USD")
        self.assertFalse(wrong_currency["authorized"])

    def test_delegated_approval_and_amount_cap(self):
        org = self.orgs[0]; _, delegatee, g, b, d = bundle(org)
        ok = evaluate(org, g, b, d, actor_id=delegatee, action="contract",
                      permission="approve", as_of="2026-06-01",
                      amount=20000, delegated=True)
        self.assertTrue(ok["authorized"])
        over = evaluate(org, g, b, d, actor_id=delegatee, action="contract",
                        permission="approve", as_of="2026-06-01",
                        amount=20001, delegated=True)
        self.assertFalse(over["authorized"])

    def test_job_title_does_not_create_authority(self):
        org = self.orgs[0]; actor, _, g, b, d = bundle(org)
        no_evidence = evaluate(org, [], [], [], actor_id=actor, action="contract",
                               permission="final_decision", as_of="2026-06-01")
        self.assertFalse(no_evidence["authorized"])

    def test_cross_organization_grant_rejected(self):
        org = self.orgs[0]; actor, _, g, b, d = bundle(org)
        bad = copy.deepcopy(g); bad[0]["org_id"] = self.orgs[1]["organization_id"]
        with self.assertRaises(ValueError):
            validate_bundle(org, bad, b, d)

    def test_expired_and_revoked_grants_rejected_at_decision_time(self):
        org = self.orgs[0]; actor, _, g, b, d = bundle(org)
        expired = copy.deepcopy(g); expired[0]["valid_until"] = "2026-05-01"
        self.assertFalse(evaluate(org, expired, b, d, actor_id=actor,
                                  action="contract", permission="final_decision",
                                  as_of="2026-06-01")["authorized"])
        revoked = copy.deepcopy(g); revoked[0]["revoked_at"] = "2026-05-01"
        self.assertFalse(evaluate(org, revoked, b, d, actor_id=actor,
                                  action="contract", permission="final_decision",
                                  as_of="2026-06-01")["authorized"])

    def test_unknown_actor_rejected(self):
        org = self.orgs[0]; _, _, g, b, d = bundle(org)
        result = evaluate(org, g, b, d, actor_id="UNKNOWN", action="contract",
                          permission="final_decision", as_of="2026-06-01")
        self.assertFalse(result["authorized"])
        self.assertEqual(result["reason"], "unknown_person")

    def test_same_seed_same_authority_ids(self):
        org = self.orgs[0]; actor, delegatee, g, b, d = bundle(org)
        again = build_organizations(seed=42, count=20, config=copy.deepcopy(CONFIG))[0]
        self.assertEqual(bundle(again), (actor, delegatee, g, b, d))


if __name__ == "__main__":
    unittest.main()
