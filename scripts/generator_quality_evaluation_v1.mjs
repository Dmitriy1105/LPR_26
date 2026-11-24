import assert from "node:assert/strict";
import { generateCommunications, validateCommunications } from "./scenario_communication_generator_v1.mjs";
import { validate as validateWorld } from "./scenario_engine_v4.mjs";
import { buildGroundTruth, validateGroundTruth } from "./scenario_ground_truth_v1.mjs";

const seeds = [0, 1, 7, 19, 42, 2026, 99173, 4294967295];
const rows = [];
const allSignatures = new Set();
let totalEvents = 0, totalActivities = 0, totalGold = 0;
let integrityErrors = 0, eventSemanticErrors = 0, goldErrors = 0;
let uniqueBodyTotal = 0, sameSeedReplayPass = true;
const eventTypes = new Set();

function ratio(n, d) { return d ? Number((n / d).toFixed(4)) : 0; }
function normalized(s) { return s.toLowerCase().replace(/[^\\p{L}\\p{N}]+/gu, " ").trim(); }

for (const seed of seeds) {
  const dataset = generateCommunications({ seed });
  const replay = generateCommunications({ seed });
  const worldCheck = validateWorld(dataset.world);
  const activityCheck = validateCommunications(dataset);
  const gold = buildGroundTruth(dataset);
  const goldCheck = validateGroundTruth(dataset, gold);
  if (JSON.stringify(dataset.communications) !== JSON.stringify(replay.communications)) sameSeedReplayPass = false;

  integrityErrors += worldCheck.errors.length + activityCheck.errors.length;
  goldErrors += goldCheck.errors.length;
  const eventById = new Map(dataset.world.events.map(e => [e.id, e]));
  const activityByEvent = new Map(dataset.communications.map(a => [a.SOURCE_EVENT_ID, a]));
  const goldByEvent = new Map(gold.records.map(g => [g.event_id, g]));
  const seenTemplates = new Set();

  for (const event of dataset.world.events) {
    eventTypes.add(event.type);
    const activity = activityByEvent.get(event.id);
    const truth = goldByEvent.get(event.id);
    if (!activity || !truth || activity.EVENT_TYPE !== event.type ||
        activity.AUTHOR_ID !== event.actor_id || truth.actor_contact_id !== event.actor_id ||
        truth.decision_maker_contact_id !== (["approve", "reject"].includes(event.type) ? event.actor_id : null) ||
        truth.executor_contact_id !== (["complete_task", "revise"].includes(event.type) ? event.actor_id : null)) {
      eventSemanticErrors++;
    }
  }
  for (const a of dataset.communications) {
    seenTemplates.add(normalized(a.DESCRIPTION.split(" Сделка: ")[0]));
  }
  uniqueBodyTotal += seenTemplates.size;
  totalEvents += dataset.world.events.length;
  totalActivities += dataset.communications.length;
  totalGold += gold.records.length;
  allSignatures.add(JSON.stringify(dataset.world.events));
  rows.push({
    seed, organizations: dataset.organization_count, deals: dataset.deal_count,
    events: dataset.event_count, communications: dataset.communication_count,
    ground_truth_records: gold.records.length, unique_text_bodies: seenTemplates.size,
    structural_pass: worldCheck.pass && activityCheck.pass,
    ground_truth_pass: goldCheck.pass
  });
}

const structural = ratio(seeds.length - rows.filter(r => !r.structural_pass).length, seeds.length);
const attribution = ratio(seeds.length - rows.filter(r => !r.ground_truth_pass).length, seeds.length);
const semantic = ratio(Math.max(0, totalEvents - eventSemanticErrors), totalEvents);
const coverage = ratio(totalActivities, totalEvents);
const diversity = ratio(uniqueBodyTotal, totalActivities);
const reproducibility = sameSeedReplayPass ? 1 : 0;
const seedVariation = allSignatures.size > 1 ? 1 : 0;
const hardGates = {
  structural_integrity: integrityErrors === 0,
  event_communication_coverage: totalActivities === totalEvents,
  event_semantic_projection: eventSemanticErrors === 0,
  ground_truth_consistency: goldErrors === 0 && totalGold === totalEvents,
  deterministic_replay: sameSeedReplayPass,
  seed_variation: allSignatures.size > 1
};
const dimensions = {
  structural_integrity: { score: structural, weight: 0.25, status: structural === 1 ? "PASS" : "FAIL" },
  event_communication_coverage: { score: coverage, weight: 0.15, status: coverage === 1 ? "PASS" : "FAIL" },
  event_semantic_projection: { score: semantic, weight: 0.2, status: semantic === 1 ? "PASS" : "FAIL" },
  ground_truth_consistency: { score: attribution, weight: 0.15, status: attribution === 1 ? "PASS" : "FAIL" },
  text_diversity: { score: diversity, weight: 0.1, status: "MEASURED_REVIEW" },
  deterministic_replay: { score: reproducibility, weight: 0.1, status: reproducibility === 1 ? "PASS" : "FAIL" },
  seed_variation: { score: seedVariation, weight: 0.05, status: seedVariation === 1 ? "PASS" : "FAIL" }
};
const weightedScore = Number(Object.values(dimensions).reduce((sum, d) => sum + d.score * d.weight, 0).toFixed(4));
const unassessed = [
  "executable BPMN trace equivalence for this scenario generator",
  "independent natural-language semantic review",
  "real-company distributional fidelity",
  "agent behavior realism",
  "NLP downstream precision/recall against held-out annotations"
];
const report = {
  schema_version: "1.0.0",
  evaluation: "Generator v4.0 synthetic scenario baseline",
  generated_at: new Date().toISOString(),
  synthetic_only: true,
  seeds,
  totals: { events: totalEvents, communications: totalActivities, ground_truth_records: totalGold, event_types: eventTypes.size },
  weighted_score: weightedScore,
  score_scale: "0..1; diagnostic only, not a certification",
  dimensions,
  hard_gates: hardGates,
  hard_gates_pass: Object.values(hardGates).every(Boolean),
  unassessed,
  seed_results: rows,
  decision: Object.values(hardGates).every(Boolean) ? "REVIEW" : "REJECTED",
  limitations: [
    "text diversity is measured by normalized exact uniqueness, not semantic quality",
    "the scenario generator is not yet proven equivalent to the executable BPMN event journal",
    "synthetic Ground Truth is constructed from the same scenario source and is not independent real-world truth"
  ]
};
console.log(JSON.stringify(report, null, 2));
assert.ok(report.hard_gates_pass, "one or more mandatory Generator Quality hard gates failed");
