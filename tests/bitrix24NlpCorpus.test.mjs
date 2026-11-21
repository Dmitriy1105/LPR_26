import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {generateFixtures} from '../scripts/generate_bitrix24_contract_fixtures.mjs';
import {generateNlpCorpus} from '../scripts/generate_bitrix24_nlp_corpus.mjs';
const read = path => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
const crm = read('../src/data/crm.json');
const bank = read('../src/data/synthetic/bank_ml_v2.json');
const corpus = generateNlpCorpus(crm, bank);
const fixtures = generateFixtures(crm, bank);

test('all calls, emails and meetings have text documents linked to REST activity IDs', () => {
  assert.equal(corpus.documents.length,bank.calls.length+bank.emails.length+bank.meetings.length);
  assert.equal(new Set(corpus.documents.map(d=>d.id)).size,corpus.documents.length);
  const ids = new Set(Object.values(fixtures.mapping.activityIds).map(String));
  for(const d of corpus.documents) {
    assert.ok(ids.has(d.crmActivityId),d.id);
    assert.ok(d.fullText.length>40,d.id);
    assert.equal(d.synthetic,true);
    assert.ok(d.contactId);
  }
});

test('transcripts have timed speaker turns; emails have body and correspondence fields',()=>{
  for(const d of corpus.documents){
    if(d.documentType==='email'){
      assert.ok(d.body.length>40);
      assert.ok(d.from && d.to && d.subject);
    } else {
      assert.ok(d.utterances.length>=2);
      for(const u of d.utterances){
        assert.ok(u.speakerName && u.text);
        assert.ok(u.endMs>u.startMs);
      }
    }
  }
});

test('NLP generation is deterministic',()=>{
  assert.deepEqual(generateNlpCorpus(crm,bank),corpus);
});
