import { createHash } from "node:crypto";
import { generateCommunications } from "./scenario_communication_generator_v1.mjs";
import { buildGroundTruth } from "./scenario_ground_truth_v1.mjs";

export const ATTRIBUTION_SCHEMA_VERSION = "1.0.0";
const EXECUTION_TYPES = new Set(["complete_task", "revise"]);
const DECISION_TYPES = new Set(["approve", "reject"]);

const sha256 = text => createHash("sha256").update(text, "utf8").digest("hex");
const unique = xs => [...new Set(xs)];

export function buildAttributionDataset(dataset, gold = buildGroundTruth(dataset)) {
  const events = new Map(dataset.world.events.map(e => [e.id, e]));
  const comms = new Map(dataset.communications.map(c => [c.SOURCE_EVENT_ID, c]));
  const goldByEvent = new Map(gold.records.map(r => [r.event_id, r]));
  const records = dataset.world.events.map(event => {
    const communication = comms.get(event.id);
    const truth = goldByEvent.get(event.id);
    if (!communication || !truth) throw new Error("missing source projection for " + event.id);
    const participants = unique(communication.COMMUNICATIONS);
    const executor = EXECUTION_TYPES.has(event.type) ? event.actor_id : null;
    const decisionMaker = DECISION_TYPES.has(event.type) ? event.actor_id : null;
    const evidence = {
      source_ref: communication.ID,
      source_event_id: event.id,
      source_type: communication.CHANNEL,
      text_sha256: sha256(communication.DESCRIPTION),
      span_status: "not_annotated"
    };
    return {
      attribution_id: "ATTR:" + event.id,
      event_id: event.id,
      deal_id: event.deal_id,
      organization_id: event.org,
      occurred_at: event.occurred_at,
      participant_contact_ids: participants,
      utterance_author_contact_id: communication.AUTHOR_ID,
      speaker_contact_id: null,
      speaker_status: "unknown_no_turn_annotation",
      action_executor_contact_id: executor,
      executor_status: executor ? "synthetic_by_construction" : "not_applicable",
      addressee_contact_ids: event.target_id ? [event.target_id] : [],
      target_contact_id: event.target_id,
      decision_maker_contact_id: decisionMaker,
      decision_status: decisionMaker ? "synthetic_by_construction" : "not_applicable",
      decision_outcome: decisionMaker ? event.type : null,
      authority_grant_refs: decisionMaker ? truth.authority_grant_refs : [],
      confirming_source_ref: communication.ID,
      evidence_refs: [evidence],
      annotation_origin: "scenario_engine_v4",
      visibility: "evaluation_only"
    };
  });
  const result = { schema_version: ATTRIBUTION_SCHEMA_VERSION, synthetic: true,
    seed: dataset.seed, records };
  const validation = validateAttributionDataset(dataset, result, gold);
  if (!validation.pass) throw new Error(validation.errors.join("; "));
  return result;
}

export function validateAttributionDataset(dataset, attribution, gold = buildGroundTruth(dataset)) {
  const errors = [];
  const check = (ok, message) => { if (!ok) errors.push(message); };
  const events = new Map(dataset.world.events.map(e => [e.id, e]));
  const comms = new Map(dataset.communications.map(c => [c.SOURCE_EVENT_ID, c]));
  const truths = new Map(gold.records.map(r => [r.event_id, r]));
  const ids = new Set();
  check(attribution.schema_version === ATTRIBUTION_SCHEMA_VERSION, "schema version mismatch");
  check(attribution.synthetic === true && attribution.seed === dataset.seed, "dataset provenance mismatch");
  check(attribution.records.length === dataset.world.events.length, "event coverage mismatch");
  for (const row of attribution.records) {
    check(!ids.has(row.attribution_id), "duplicate attribution id");
    ids.add(row.attribution_id);
    const event = events.get(row.event_id), comm = comms.get(row.event_id), truth = truths.get(row.event_id);
    check(!!event && !!comm && !!truth, "orphan attribution " + row.event_id);
    if (!event || !comm || !truth) continue;
    check(row.deal_id === event.deal_id && row.organization_id === event.org, "entity scope mismatch " + row.event_id);
    check(row.occurred_at === event.occurred_at, "event timestamp mismatch " + row.event_id);
    check(JSON.stringify(row.participant_contact_ids) === JSON.stringify(unique(comm.COMMUNICATIONS)), "participant mismatch " + row.event_id);
    check(row.utterance_author_contact_id === comm.AUTHOR_ID && comm.AUTHOR_ID === event.actor_id, "author attribution mismatch " + row.event_id);
    check(row.speaker_contact_id === null && row.speaker_status === "unknown_no_turn_annotation", "unsupported speaker attribution " + row.event_id);
    const expectedExecutor = EXECUTION_TYPES.has(event.type) ? event.actor_id : null;
    check(row.action_executor_contact_id === expectedExecutor, "executor semantics mismatch " + row.event_id);
    const expectedDecisionMaker = DECISION_TYPES.has(event.type) ? event.actor_id : null;
    check(row.decision_maker_contact_id === expectedDecisionMaker, "decision-maker semantics mismatch " + row.event_id);
    check(row.decision_outcome === (expectedDecisionMaker ? event.type : null), "decision outcome mismatch " + row.event_id);
    check(JSON.stringify(row.authority_grant_refs) === JSON.stringify(truth.authority_grant_refs), "authority evidence mismatch " + row.event_id);
    check(row.confirming_source_ref === comm.ID, "confirming source mismatch " + row.event_id);
    check(row.evidence_refs.length === 1 && row.evidence_refs[0].source_ref === comm.ID, "evidence source mismatch " + row.event_id);
    check(row.evidence_refs[0].text_sha256 === sha256(comm.DESCRIPTION), "evidence digest mismatch " + row.event_id);
    check(row.visibility === "evaluation_only" && row.annotation_origin === "scenario_engine_v4", "gold visibility/provenance mismatch");
  }
  return { pass: errors.length === 0, errors, records: attribution.records.length,
    event_coverage: ids.size === dataset.world.events.length,
    text_entailment_verified: false, speaker_turns_annotated: false };
}

export function audit(seed = 42, organizations = 5, dealsPerOrganization = 6) {
  const dataset = generateCommunications({ seed, organizations, dealsPerOrganization });
  const gold = buildGroundTruth(dataset);
  const attribution = buildAttributionDataset(dataset, gold);
  return { status: "PASS", seed, organizations, deals: dataset.world.deals.length,
    events: dataset.world.events.length, communications: dataset.communications.length,
    attribution_records: attribution.records.length,
    speaker_turns_annotated: false, text_entailment_verified: false,
    scope: "in-memory structured attribution QC only; no persistent dataset generation" };
}
