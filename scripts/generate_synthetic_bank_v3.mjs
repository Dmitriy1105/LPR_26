// Synthetic bank dataset v3.
// Keeps the normalized bank_ml_v2 schema and adds richer multi-party events.
// Run: node scripts/generate_synthetic_bank_v3.mjs
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { generateV2 } from "./generate_synthetic_bank_v2.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const AS_OF = "2026-11-21";

function isoDate(value) {
  return new Date(value + "T12:00:00Z").toISOString().slice(0, 10);
}
function addDays(value, days) {
  const d = new Date(value + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}
function dayDiff(a, b) {
  return Math.round((Date.parse(b + "T00:00:00Z") - Date.parse(a + "T00:00:00Z")) / 86400000);
}
function unique(values) {
  return [...new Set(values.filter(Boolean))];
}
function stablePick(values, index) {
  return values[((index % values.length) + values.length) % values.length];
}

export function generateV3(crm, v1, seed = 20261122) {
  const bank = generateV2(crm, v1, seed);
  const people = crm.people.filter(p => p.companyId === "bank");
  const peopleById = new Map(people.map(p => [p.id, p]));
  const opportunitiesById = new Map(bank.opportunities.map(o => [o.id, o]));
  const templates = [
    "Участники обсудили критерии выбора решения и распределили дальнейшие действия.",
    "Стороны сверили технические ограничения, бюджетные условия и порядок согласования.",
    "Зафиксированы позиции подразделений; окончательное решение отложено до получения дополнительных материалов.",
    "Обсуждены замечания участников и необходимые проверки перед следующим этапом."
  ];

  // Expand participant lists on existing decision meetings. The original
  // fields and normalized record structure are preserved.
  for (let i = 0; i < bank.decisionMeetings.length; i++) {
    const meeting = bank.decisionMeetings[i];
    const opp = opportunitiesById.get(meeting.opportunityId);
    if (!opp) throw new Error("Unknown opportunity for " + meeting.id);

    const candidates = unique([
      opp.primaryPersonId,
      ...(opp.stakeholderIds || []),
      ...(meeting.clientAttendeeIds || [])
    ]).filter(id => peopleById.has(id));

    const desiredCount = Math.min(candidates.length, 2 + (i % 3));
    const ordered = [
      opp.primaryPersonId,
      ...candidates.filter(id => id !== opp.primaryPersonId)
    ];
    const attendees = unique(ordered).slice(0, desiredCount);
    if (attendees.length < 2) {
      throw new Error("Decision meeting must have at least two client attendees: " + meeting.id);
    }

    meeting.clientAttendeeIds = attendees;
    meeting.minutes = templates[i % templates.length] +
      (meeting.minutes ? " " + meeting.minutes : "");
    meeting.synthetic = true;
  }

  // Add one additional internal client message per opportunity. It uses the
  // existing clientInternalMessages record schema and does not alter REST
  // response field names.
  const extraMessages = [];
  for (let i = 0; i < bank.opportunities.length; i++) {
    const opp = bank.opportunities[i];
    const ids = unique([...(opp.stakeholderIds || []), opp.primaryPersonId])
      .filter(id => peopleById.has(id));
    if (ids.length < 2) continue;

    const fromPersonId = stablePick(ids, i);
    let toPersonId = stablePick(ids, i + 1);
    if (toPersonId === fromPersonId) toPersonId = stablePick(ids, i + 2);
    if (toPersonId === fromPersonId) continue;

    const createdDate = opp.createdDate || AS_OF;
    const maxDays = Math.max(1, dayDiff(createdDate, opp.closedDate || AS_OF));
    const date = addDays(createdDate, Math.floor(maxDays * (0.35 + (i % 4) * 0.1)));
    if (date > AS_OF) throw new Error("Generated future internal message " + opp.id);

    extraMessages.push({
      id: "internal-v3-" + opp.id,
      companyId: "bank",
      opportunityId: opp.id,
      date,
      fromPersonId,
      toPersonId,
      channel: ["internal_email", "meeting_note", "internal_chat"][i % 3],
      topic: ["Проверка требований", "Бюджет и условия", "Согласование решения", "Риски внедрения"][i % 4],
      summary: [
        "Участники обменялись замечаниями и договорились о дополнительной проверке.",
        "Коллеги обсудили ограничения и определили, какие сведения нужны для решения.",
        "Зафиксированы разные позиции подразделений; требуется согласование.",
        "Один участник рекомендовал подключить коллегу с профильной компетенцией."
      ][i % 4],
      synthetic: true
    });
  }
  bank.clientInternalMessages.push(...extraMessages);

  // Keep eventIndex synchronized with the expanded attendee lists.
  const eventBySourceId = new Map(bank.eventIndex.map(e => [e.sourceId, e]));
  for (const meeting of bank.decisionMeetings) {
    const event = eventBySourceId.get(meeting.id);
    if (event) event.personIds = unique(meeting.clientAttendeeIds);
  }
  for (const message of extraMessages) {
    bank.eventIndex.push({
      id: "event-" + message.id,
      sourceId: message.id,
      kind: "client_internal",
      date: message.date,
      companyId: "bank",
      personIds: unique([message.fromPersonId, message.toPersonId]),
      opportunityId: message.opportunityId,
      synthetic: true
    });
  }
  bank.eventIndex.sort((a, b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id));

  bank.metadata = {
    ...bank.metadata,
    dataset: "lpr_bank_synthetic_v3",
    version: 3,
    seed,
    asOf: AS_OF,
    parentDataset: "lpr_bank_synthetic_v2",
    compatibility: "normalized_v2_schema_additive_records",
    warning: "ALL DATA FICTIONAL. NOT REAL CLIENT ACTIVITY, FINANCE OR VALIDATED ML LABELS."
  };

  const allPeopleIds = new Set(people.map(p => p.id));
  const errors = [];
  const allRecordIds = new Set();
  for (const key of ["decisionMeetings", "clientInternalMessages", "eventIndex"]) {
    for (const row of bank[key] || []) {
      if (!row.id) errors.push("Missing ID in " + key);
      if (allRecordIds.has(row.id) && key !== "eventIndex") errors.push("Duplicate generated ID " + row.id);
      allRecordIds.add(row.id);
    }
  }
  for (const meeting of bank.decisionMeetings) {
    const ids = unique(meeting.clientAttendeeIds || []);
    if (ids.length < 2) errors.push("Meeting has fewer than two client participants: " + meeting.id);
    for (const id of ids) if (!allPeopleIds.has(id)) errors.push("Unknown meeting participant " + id);
  }
  for (const message of bank.clientInternalMessages) {
    if (message.fromPersonId === message.toPersonId) errors.push("Self-message " + message.id);
    for (const id of [message.fromPersonId, message.toPersonId]) {
      if (!allPeopleIds.has(id)) errors.push("Unknown message participant " + id);
    }
  }
  for (const event of bank.eventIndex) {
    for (const id of event.personIds || []) if (!allPeopleIds.has(id)) errors.push("Unknown event participant " + id);
  }
  if (errors.length) throw new Error(errors.slice(0, 20).join("; "));

  const groundTruth = {
    synthetic: true,
    dataset: "lpr_bank_synthetic_v3_ground_truth",
    version: 3,
    warning: "EVALUATION ONLY. MUST NOT BE USED AS NLP INPUT FEATURES OR INFERENCE CONTEXT.",
    excludedFromNlpInputs: true,
    participantTruth: [
      ...bank.decisionMeetings.map(m => ({
        sourceId: m.id, eventType: "decision_meeting",
        participantContactIds: unique(m.clientAttendeeIds),
        expectedParticipantCount: unique(m.clientAttendeeIds).length
      })),
      ...bank.clientInternalMessages.map(m => ({
        sourceId: m.id, eventType: "client_internal",
        participantContactIds: unique([m.fromPersonId, m.toPersonId]),
        senderContactId: m.fromPersonId,
        recipientContactId: m.toPersonId
      }))
    ],
    roleTruth: people.map(p => ({
      contactId: p.id,
      decisionRole: p.decisionRole,
      department: p.department,
      title: p.title
    })),
    organizationalRelationTruth: crm.relations
      .filter(r => r.companyId === "bank")
      .map(r => ({
        relationId: r.id, sourceContactId: r.from,
        targetContactId: r.to, relationType: r.type,
        source: "CRM_SYNTHETIC_GROUND_TRUTH"
      }))
  };

  return { bank, groundTruth };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const crm = JSON.parse(readFileSync(resolve(root, "src/data/crm.json"), "utf8"));
  const v1 = JSON.parse(readFileSync(resolve(root, "src/data/synthetic/bank_ml_v1.json"), "utf8"));
  const { bank, groundTruth } = generateV3(crm, v1);
  const bankPath = resolve(root, "src/data/synthetic/bank_ml_v3.json");
  const truthPath = resolve(root, "src/data/synthetic/bank_ml_v3_ground_truth.json");
  mkdirSync(dirname(bankPath), { recursive: true });
  writeFileSync(bankPath, JSON.stringify(bank, null, 2) + "\n", "utf8");
  writeFileSync(truthPath, JSON.stringify(groundTruth, null, 2) + "\n", "utf8");
  console.log("Generated bank_ml_v3.json", {
    opportunities: bank.opportunities.length,
    decisionMeetings: bank.decisionMeetings.length,
    clientInternalMessages: bank.clientInternalMessages.length,
    multiParticipantMeetings: bank.decisionMeetings.filter(m => new Set(m.clientAttendeeIds).size >= 2).length,
    groundTruthParticipants: groundTruth.participantTruth.length
  });
}
