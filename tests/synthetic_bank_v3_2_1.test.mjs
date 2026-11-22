import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { diversifyActivities } from "../scripts/generate_synthetic_bank_v3_2_1.mjs";

const root = resolve(process.cwd());
const data = resolve(root, "src/data/bitrix24_contract_v2");
const read = p => JSON.parse(readFileSync(resolve(data, p), "utf8"));
const manifest = read("manifest.json");
const contacts = read("contacts/page_001.json").result.items;
const pages = manifest.methods.find(x => x.key === "activities").pages.map(x => read(x.file));
const rows = pages.flatMap(x => x.result);

test("v3.2.1 preserves REST counts and activity distribution", () => {
  assert.equal(manifest.generatorVersion, "3.2.1");
  assert.equal(manifest.recordCounts.activities, 630);
  assert.equal(rows.length, 630);
  assert.equal(rows.filter(x => x.TYPE_ID === "2").length, 180);
  assert.equal(rows.filter(x => x.TYPE_ID === "4").length, 324);
  assert.equal(rows.filter(x => x.TYPE_ID === "1").length, 126);
});

test("all email descriptions are non-empty and exact-text unique", () => {
  const emails = rows.filter(x => x.TYPE_ID === "4");
  assert.ok(emails.every(x => typeof x.DESCRIPTION === "string" && x.DESCRIPTION.trim()));
  const normalized = emails.map(x => x.DESCRIPTION.toLowerCase().replace(/\\s+/g, " ").trim());
  assert.equal(new Set(normalized).size, emails.length);
});

test("generator is deterministic and preserves IDs and COMMUNICATIONS", () => {
  const cloned = JSON.parse(JSON.stringify(pages));
  const generated = diversifyActivities(cloned, contacts, 20261123);
  assert.equal(generated.rewritten, 324);
  assert.deepEqual(generated.rows, rows);
});

test("all communication references resolve to known contacts", () => {
  const known = new Set(contacts.map(x => String(x.id)));
  for (const row of rows) {
    assert.ok(Array.isArray(row.COMMUNICATIONS));
    assert.ok(row.COMMUNICATIONS.length >= 1);
    for (const ref of row.COMMUNICATIONS) assert.ok(known.has(String(ref.ENTITY_ID)));
  }
});
