import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { generateV3 } from "../scripts/generate_synthetic_bank_v3.mjs";
import { generateFixturesV2 } from "../scripts/generate_bitrix24_contract_fixtures_v2.mjs";

const root = resolve(process.cwd());
const crm = JSON.parse(readFileSync(resolve(root, "src/data/crm.json"), "utf8"));
const v1 = JSON.parse(readFileSync(resolve(root, "src/data/synthetic/bank_ml_v1.json"), "utf8"));

test("v3 preserves base normalized collections and adds multiparty records", () => {
  const { bank, groundTruth } = generateV3(crm, v1);
  assert.equal(bank.metadata.version, 3);
  assert.equal(bank.calls.length, v1.calls.length);
  assert.equal(bank.emails.length, v1.emails.length);
  assert.equal(bank.meetings.length, v1.meetings.length);
  assert.ok(bank.decisionMeetings.length > 0);
  assert.ok(bank.decisionMeetings.every(m => new Set(m.clientAttendeeIds).size >= 2));
  assert.ok(bank.clientInternalMessages.every(m => m.fromPersonId !== m.toPersonId));
  assert.ok(groundTruth.excludedFromNlpInputs);
  assert.ok(groundTruth.participantTruth.length >= bank.decisionMeetings.length);
});

test("Bitrix24 legacy REST activity shape carries multiple COMMUNICATIONS", () => {
  const { bank } = generateV3(crm, v1);
  const fixtures = generateFixturesV2(crm, bank);
  const activities = fixtures.activityRecords;
  assert.ok(activities.length > v1.calls.length + v1.emails.length + v1.meetings.length);
  assert.ok(activities.every(a =>
    typeof a.ID === "string" &&
    typeof a.OWNER_ID === "string" &&
    a.OWNER_TYPE_ID === "3" &&
    Array.isArray(a.COMMUNICATIONS)
  ));
  const multi = activities.filter(a => a.COMMUNICATIONS.length >= 2);
  assert.ok(multi.length > 0);
  assert.ok(multi.every(a => a.COMMUNICATIONS.every(c =>
    typeof c.ID === "string" && typeof c.ENTITY_ID === "string" &&
    c.ENTITY_TYPE_ID === "3" && typeof c.TYPE === "string" &&
    typeof c.VALUE === "string"
  )));
  assert.equal(fixtures.manifest.profile, "legacy-rest-v1");
  assert.equal(fixtures.manifest.recordCounts.activities, activities.length);
});

test("all activity communications resolve to known CRM contacts", () => {
  const { bank } = generateV3(crm, v1);
  const fixtures = generateFixturesV2(crm, bank);
  const valid = new Set(Object.values(fixtures.mapping.contactIds).map(String));
  for (const activity of fixtures.activityRecords) {
    for (const communication of activity.COMMUNICATIONS) {
      assert.ok(valid.has(communication.ENTITY_ID));
    }
  }
});

test("v3.1 generates deterministic, event-specific communication text", () => {
  const first = generateV3(crm, v1, 20261122);
  const second = generateV3(crm, v1, 20261122);
  assert.equal(first.bank.metadata.generatorVersion, "3.1.0");
  assert.deepEqual(first.bank.calls, second.bank.calls);
  assert.deepEqual(first.bank.emails, second.bank.emails);
  assert.deepEqual(first.bank.meetings, second.bank.meetings);

  const fixtures = generateFixturesV2(crm, first.bank);
  const byType = new Map();
  for (const row of fixtures.activityRecords) {
    const key = row.TYPE_ID;
    if (!byType.has(key)) byType.set(key, []);
    byType.get(key).push(String(row.DESCRIPTION || "").toLowerCase().replace(/\\s+/g, " ").trim());
  }
  for (const [type, texts] of byType) {
    const uniqueCount = new Set(texts).size;
    const ratio = uniqueCount / texts.length;
    assert.ok(ratio >= 0.95, "Exact-text uniqueness below 95% for TYPE_ID " + type + ": " + ratio);
    assert.ok(texts.every(Boolean), "Empty DESCRIPTION for TYPE_ID " + type);
  }
});

test("v3.1 preserves REST counts and multiparty communication schema", () => {
  const { bank } = generateV3(crm, v1, 20261122);
  const fixtures = generateFixturesV2(crm, bank);
  assert.equal(fixtures.manifest.profile, "legacy-rest-v1");
  assert.equal(fixtures.manifest.recordCounts.activities, fixtures.activityRecords.length);
  assert.equal(fixtures.activityRecords.length, 630);
  assert.ok(fixtures.activityRecords.every(a => Array.isArray(a.COMMUNICATIONS)));
  assert.ok(fixtures.activityRecords.every(a => a.COMMUNICATIONS.length >= 1));
  assert.ok(fixtures.activityRecords.some(a => a.COMMUNICATIONS.length >= 2));
});

