import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {generateFixtures} from '../scripts/generate_bitrix24_contract_fixtures.mjs';

const read = path => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
const crm = read('../src/data/crm.json');
const bank = read('../src/data/synthetic/bank_ml_v2.json');
const output = generateFixtures(crm, bank);
const rows = key => {
  const def = output.manifest.methods.find(method => method.key === key);
  assert.ok(def, 'Missing method: ' + key);
  return def.pages.flatMap(page => {
    const payload = output.pages[page.file];
    return def.resultPath === 'result.items'
      ? payload.result.items
      : def.resultPath === 'result.tasks'
        ? payload.result.tasks
        : payload.result;
  });
};

test('every exported identifier is unique per entity type', () => {
  for (const key of ['companies', 'contacts', 'deals', 'invoices', 'activities', 'tasks']) {
    const ids = rows(key).map(item => String(item.id ?? item.ID));
    assert.equal(new Set(ids).size, ids.length, key);
    assert.ok(ids.every(id => /^\d+$/.test(id)), key);
  }
});

test('all contact, deal, activity and task owners are mapped', () => {
  const users = new Set(Object.values(output.mapping.users).map(String));
  for (const key of ['companies', 'contacts', 'deals']) {
    for (const item of rows(key)) assert.ok(users.has(String(item.assignedById)), key);
  }
  for (const item of rows('activities')) assert.ok(users.has(String(item.RESPONSIBLE_ID)));
  for (const item of rows('tasks')) assert.ok(users.has(String(item.responsibleId)));
});

test('all activities have parseable chronological timestamps', () => {
  for (const item of rows('activities')) {
    const start = Date.parse(item.START_TIME);
    const end = Date.parse(item.END_TIME);
    assert.ok(Number.isFinite(start), item.ID);
    assert.ok(Number.isFinite(end), item.ID);
    assert.ok(end >= start, item.ID);
  }
});

test('REST fixtures never expose manual analytic attributes', () => {
  const forbidden = new Set(['decisionRole', 'stance', 'influence', 'warmth',
    'manualAnnotations', 'relationshipEvents', 'personSnapshots',
    'opportunitySnapshots', 'decisionOutcomes']);
  for (const page of Object.values(output.pages)) {
    const inspect = value => {
      if (Array.isArray(value)) return value.forEach(inspect);
      if (!value || typeof value !== 'object') return;
      for (const [key, nested] of Object.entries(value)) {
        assert.ok(!forbidden.has(key), 'Forbidden REST field: ' + key);
        inspect(nested);
      }
    };
    inspect(page);
  }
});

test('all REST page pointers are contiguous and exhaustive', () => {
  for (const method of output.manifest.methods) {
    let offset = 0;
    for (const page of method.pages) {
      assert.equal(page.start, offset, method.key);
      const payload = output.pages[page.file];
      assert.equal(payload.total, method.recordCount);
      offset += page.count;
      assert.equal(payload.next, offset < method.recordCount ? offset : undefined);
    }
    assert.equal(offset, method.recordCount, method.key);
  }
});

test('contact names preserve Russian first and family name order', () => {
  const original = new Map(crm.people.filter(person => person.companyId === 'bank')
    .map(person => [output.mapping.contactIds[person.id], person.name]));
  for (const contact of rows('contacts')) {
    const parts = original.get(contact.id)?.trim().split(/\s+/);
    assert.ok(parts, String(contact.id));
    assert.equal(contact.lastName, parts[0]);
    assert.equal(contact.name, parts[1] || parts[0]);
    if (parts.length > 2) assert.equal(contact.secondName, parts.slice(2).join(' '));
  }
});
