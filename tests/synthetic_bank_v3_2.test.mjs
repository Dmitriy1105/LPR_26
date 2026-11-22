import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { generateV3_2 } from "../scripts/generate_synthetic_bank_v3_2.mjs";
import { generateFixturesV2 } from "../scripts/generate_bitrix24_contract_fixtures_v2.mjs";

const root = resolve(process.cwd());
const crm = JSON.parse(readFileSync(resolve(root, "src/data/crm.json"), "utf8"));
const v1 = JSON.parse(readFileSync(resolve(root, "src/data/synthetic/bank_ml_v1.json"), "utf8"));

test("v3.2 preserves normalized collection counts and schema", () => {
  const { bank, groundTruth } = generateV3_2(crm, v1, 20261122);
  assert.equal(bank.metadata.version, 3);
  assert.equal(bank.metadata.generatorVersion, "3.2.0");
  assert.equal(bank.calls.length, v1.calls.length);
  assert.equal(bank.emails.length, v1.emails.length);
  assert.equal(bank.meetings.length, v1.meetings.length);
  assert.ok(bank.decisionMeetings.length > 0);
  assert.ok(bank.clientInternalMessages.length > 0);
  assert.ok(groundTruth.excludedFromNlpInputs);
  assert.ok(groundTruth.participantTruth.length >= bank.decisionMeetings.length);
});

test("v3.2 is deterministic for a fixed seed", () => {
  const a = generateV3_2(crm, v1, 20261122);
  const b = generateV3_2(crm, v1, 20261122);
  assert.deepEqual(a.bank.calls, b.bank.calls);
  assert.deepEqual(a.bank.emails, b.bank.emails);
  assert.deepEqual(a.bank.meetings, b.bank.meetings);
  assert.deepEqual(a.bank.decisionMeetings, b.bank.decisionMeetings);
  assert.deepEqual(a.bank.clientInternalMessages, b.bank.clientInternalMessages);
});

test("v3.2 creates non-empty scenario-based text without gender placeholders", () => {
  const { bank } = generateV3_2(crm, v1, 20261122);
  const texts = [
    ...bank.calls.flatMap(x => (x.transcript || []).map(t => t.text)),
    ...bank.emails.map(x => x.body),
    ...bank.meetings.map(x => x.minutes),
    ...bank.decisionMeetings.map(x => x.minutes),
    ...bank.clientInternalMessages.map(x => x.summary)
  ];
  assert.ok(texts.length > 0);
  assert.ok(texts.every(x => typeof x === "string" && x.trim().length > 0));
  assert.ok(!texts.some(x => /\b(?:направил|попросил|сообщил|передал|предложил)\(а\)/i.test(x)));
});

test("REST fixtures preserve 630 activities and valid multiparty communications", () => {
  const { bank } = generateV3_2(crm, v1, 20261122);
  const fixtures = generateFixturesV2(crm, bank);
  const activities = fixtures.activityRecords;
  assert.equal(fixtures.manifest.profile, "legacy-rest-v1");
  assert.equal(activities.length, 630);
  assert.equal(fixtures.manifest.recordCounts.activities, 630);
  assert.ok(activities.every(a =>
    typeof a.ID === "string" &&
    typeof a.OWNER_ID === "string" &&
    a.OWNER_TYPE_ID === "3" &&
    Array.isArray(a.COMMUNICATIONS) &&
    a.COMMUNICATIONS.length >= 1
  ));
  assert.ok(activities.some(a => a.COMMUNICATIONS.length >= 2));
  const valid = new Set(Object.values(fixtures.mapping.contactIds).map(String));
  for (const activity of activities) {
    for (const communication of activity.COMMUNICATIONS) {
      assert.ok(valid.has(communication.ENTITY_ID));
    }
  }
});

test("REST activity descriptions retain at least 95% exact-text uniqueness by type", () => {
  const { bank } = generateV3_2(crm, v1, 20261122);
  const fixtures = generateFixturesV2(crm, bank);
  const byType = new Map();
  for (const row of fixtures.activityRecords) {
    const key = row.TYPE_ID;
    if (!byType.has(key)) byType.set(key, []);
    byType.get(key).push(String(row.DESCRIPTION || "").toLowerCase().replace(/\s+/g, " ").trim());
  }
  for (const [type, texts] of byType) {
    const ratio = new Set(texts).size / texts.length;
    assert.ok(ratio >= 0.95, "Exact-text uniqueness below 95% for TYPE_ID " + type + ": " + ratio);
    assert.ok(texts.every(Boolean), "Empty DESCRIPTION for TYPE_ID " + type);
  }
});
