import assert from "node:assert/strict";
import { generateCommunications } from "./scenario_communication_generator_v1.mjs";

const seeds = [0, 1, 7, 19, 42, 2026, 99173, 4294967295];
const normalize = value => value.toLowerCase()
  .replace(/(?:org-\\d+-d\\d+-e\\d+|org-\\d+-d\\d+|act-\\d+)/giu, " ")
  .replace(/\\b\\d+\\b/gu, " ")
  .replace(/[^\\p{L}\\p{N}]+/gu, " ").trim();
const tokens = value => new Set(normalize(value).split(/\\s+/u).filter(Boolean));
const jaccard = (a, b) => {
  const left = tokens(a), right = tokens(b);
  let intersection = 0;
  for (const token of left) if (right.has(token)) intersection++;
  return intersection / (left.size + right.size - intersection || 1);
};
const round = n => Number(n.toFixed(4));

function evaluate(seed) {
  const dataset = generateCommunications({ seed });
  const replay = generateCommunications({ seed });
  assert.deepEqual(dataset.communications, replay.communications, "same-seed replay mismatch");
  const byType = new Map();
  const bodies = dataset.communications.map(item => ({
    type: item.EVENT_TYPE,
    body: item.DESCRIPTION.split(" Сделка: ")[0].replace(/\\. Отправитель:.+$/u, "")
  }));
  for (const item of dataset.communications) {
    if (!byType.has(item.EVENT_TYPE)) byType.set(item.EVENT_TYPE, { total: 0, bodies: new Set(), subjects: new Set(), lengths: [] });
    const row = byType.get(item.EVENT_TYPE);
    row.total++;
    row.bodies.add(normalize(item.DESCRIPTION.split(" Сделка: ")[0].replace(/\\. Отправитель:.+$/u, "")));
    row.subjects.add(normalize(item.SUBJECT));
    row.lengths.push(item.DESCRIPTION.trim().split(/\\s+/u).length);
  }
  let maxSimilarity = 0, highPairs = 0, pairCount = 0;
  for (let i = 0; i < bodies.length; i++) {
    for (let j = i + 1; j < bodies.length; j++) {
      if (bodies[i].type !== bodies[j].type) continue;
      pairCount++;
      const score = jaccard(bodies[i].body, bodies[j].body);
      maxSimilarity = Math.max(maxSimilarity, score);
      if (score >= 0.85) highPairs++;
    }
  }
  const metrics = [...byType.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([event_type, row]) => ({
    event_type, communications: row.total,
    unique_body_ratio: round(row.bodies.size / row.total),
    unique_subject_ratio: round(row.subjects.size / row.total),
    mean_words: round(row.lengths.reduce((a, b) => a + b, 0) / row.lengths.length)
  }));
  return {
    seed, events: dataset.event_count, communications: dataset.communication_count,
    unique_normalized_bodies: new Set(bodies.map(x => normalize(x.body))).size,
    overall_body_ratio: round(new Set(bodies.map(x => normalize(x.body))).size / bodies.length),
    max_within_type_jaccard: round(maxSimilarity), high_similarity_pairs: highPairs,
    within_type_pairs: pairCount, event_type_metrics: metrics
  };
}

const results = seeds.map(evaluate);
const report = {
  schema_version: "2.0.0",
  audit: "GEN-010 text diversity diagnostic",
  status: "DIAGNOSTIC_ONLY",
  seeds,
  seed_results: results,
  aggregate: {
    mean_body_ratio: round(results.reduce((s, r) => s + r.overall_body_ratio, 0) / results.length),
    minimum_body_ratio: Math.min(...results.map(r => r.overall_body_ratio)),
    maximum_within_type_jaccard: Math.max(...results.map(r => r.max_within_type_jaccard)),
    high_similarity_pairs_total: results.reduce((s, r) => s + r.high_similarity_pairs, 0)
  },
  interpretation: [
    "IDs, numeric identifiers, sender and recipient suffixes are removed before lexical uniqueness is measured.",
    "Jaccard is a lexical diagnostic, not a semantic-quality score.",
    "No acceptance threshold is asserted until baseline metrics are captured."
  ]
};
console.log(JSON.stringify(report, null, 2));
