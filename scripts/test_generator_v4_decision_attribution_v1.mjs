import assert from "node:assert/strict";
import { generateCommunications } from "./scenario_communication_generator_v1.mjs";
import { buildGroundTruth } from "./scenario_ground_truth_v1.mjs";
import { buildAttributionDataset, validateAttributionDataset } from "./generator_v4_decision_attribution_v1.mjs";

const dataset = generateCommunications({ seed: 42, organizations: 5, dealsPerOrganization: 6 });
const gold = buildGroundTruth(dataset);
const attribution = buildAttributionDataset(dataset, gold);
assert.equal(attribution.records.length, dataset.world.events.length);
assert.equal(validateAttributionDataset(dataset, attribution, gold).pass, true);
assert.deepEqual(attribution, buildAttributionDataset(generateCommunications({ seed: 42, organizations: 5, dealsPerOrganization: 6 })));

const checks = [
  x => { x.records[0].participant_contact_ids = ["UNKNOWN"]; },
  x => { x.records[0].utterance_author_contact_id = "UNKNOWN"; },
  x => { x.records[0].speaker_contact_id = x.records[0].utterance_author_contact_id; },
  x => { x.records.find(r => r.action_executor_contact_id !== null).action_executor_contact_id = "UNKNOWN"; },
  x => { x.records.find(r => r.decision_maker_contact_id !== null).authority_grant_refs = []; },
  x => { x.records[0].confirming_source_ref = "WRONG"; },
  x => { x.records[0].evidence_refs[0].text_sha256 = "0".repeat(64); },
  x => { x.records.pop(); },
  x => { x.records[0].organization_id = "ORG-999"; }
];
for (const mutate of checks) {
  const bad = structuredClone(attribution);
  mutate(bad);
  assert.equal(validateAttributionDataset(dataset, bad, gold).pass, false);
}
const summary = {
  status: "PASS",
  organizations: dataset.world.organizations.length,
  deals: dataset.world.deals.length,
  events: dataset.world.events.length,
  attribution_records: attribution.records.length,
  positive_cases: 3,
  negative_cases: checks.length,
  deterministic: true,
  speaker_turns_annotated: false,
  text_entailment_verified: false
};
console.log(JSON.stringify(summary));
