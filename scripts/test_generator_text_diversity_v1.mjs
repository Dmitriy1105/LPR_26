import assert from "node:assert/strict";
import { generateCommunications } from "./scenario_communication_generator_v1.mjs";

const seeds = [42, 7, 19, 2026, 99173];
const normalize = value => value.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
const tokens = value => new Set(normalize(value).split(/\s+/).filter(Boolean));
const jaccard = (left, right) => {
  const a = tokens(left), b = tokens(right);
  let intersection = 0;
  for (const token of a) if (b.has(token)) intersection++;
  return intersection / (a.size + b.size - intersection || 1);
};

function evaluate(seed) {
  const dataset = generateCommunications({ seed });
  const groups = new Map();
  const normalizedBodies = new Set();
  for (const activity of dataset.communications) {
    const body = activity.DESCRIPTION.split(" Сделка: ")[0].trim();
    const subject = activity.SUBJECT.replace(/\s+ORG-\d+-D\d+$/, "").trim();
    if (!groups.has(activity.EVENT_TYPE)) groups.set(activity.EVENT_TYPE, {
      bodies: new Set(), subjects: new Set(), count: 0
    });
    const group = groups.get(activity.EVENT_TYPE);
    group.count++;
    group.bodies.add(normalize(body));
    group.subjects.add(normalize(subject));
    normalizedBodies.add(normalize(body));
  }
  const rows = [...groups.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([event_type, group]) => ({
    event_type, communications: group.count,
    unique_body_variants: group.bodies.size,
    unique_subject_variants: group.subjects.size
  }));
  const messages = dataset.communications.map(activity => ({
    type: activity.EVENT_TYPE,
    body: activity.DESCRIPTION.split(" Сделка: ")[0].trim()
  }));
  let maxSimilarity = 0, highSimilarityPairs = 0;
  for (let i = 0; i < messages.length; i++) {
    for (let j = i + 1; j < messages.length; j++) {
      if (messages[i].type !== messages[j].type) continue;
      const similarity = jaccard(messages[i].body, messages[j].body);
      maxSimilarity = Math.max(maxSimilarity, similarity);
      if (similarity >= 0.85) highSimilarityPairs++;
    }
  }
  return { dataset, rows, uniqueBodies: normalizedBodies.size, maxSimilarity, highSimilarityPairs };
}

const results = seeds.map(seed => ({ seed, ...evaluate(seed) }));
for (const result of results) {
  assert.equal(result.dataset.communications.length, result.dataset.event_count);
  assert.equal(result.rows.length, 10);
  assert.ok(result.uniqueBodies >= 100,
    "fewer than 100 unique contextual message bodies for seed " + result.seed + ": " + result.uniqueBodies);
  assert.ok(result.rows.every(row => row.unique_body_variants >= 2),
    "event type has fewer than 2 body variants for seed " + result.seed);
  assert.ok(result.dataset.communications.every(activity =>
    !/(decision_maker_contact_id|authority_grant_refs|ground.?truth)/i.test(activity.DESCRIPTION)),
    "gold metadata leaked into communication text");
  const replay = generateCommunications({ seed: result.seed });
  assert.deepEqual(replay.communications, result.dataset.communications,
    "non-deterministic replay for seed " + result.seed);
}
assert.notDeepEqual(results[0].dataset.communications, results[1].dataset.communications,
  "different seeds did not change communication rendering");

const report = {
  status: "PASS",
  seeds: results.map(result => result.seed),
  communications_per_seed: results.map(result => result.dataset.communications.length),
  unique_contextual_bodies_per_seed: results.map(result => result.uniqueBodies),
  event_type_metrics: results.map(result => ({ seed: result.seed, metrics: result.rows })),
  max_within_type_jaccard: Math.max(...results.map(result => result.maxSimilarity)),
  high_similarity_pairs: results.reduce((sum, result) => sum + result.highSimilarityPairs, 0),
  deterministic_replay: true,
  cross_seed_variation: true,
  gold_label_leakage: false,
  method: "Unicode-normalized exact uniqueness plus token Jaccard; not a substitute for independent semantic review"
};
console.log(JSON.stringify(report, null, 2));
