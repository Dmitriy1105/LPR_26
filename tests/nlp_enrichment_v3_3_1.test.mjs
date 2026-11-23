import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const dir='src/data/nlp_enrichment_v3_3_1/';
const scenarios=JSON.parse(fs.readFileSync(dir+'scenarios.json'));
const gold=JSON.parse(fs.readFileSync(dir+'ground_truth.json'));
const predicted=JSON.parse(fs.readFileSync(dir+'extracted_relations.json'));
test('dataset integrity',()=>{
 assert.equal(scenarios.length,90);
 assert.equal(gold.length,90);
 assert.equal(new Set(scenarios.map(x=>x.activity_id)).size,90);
});
test('text evidence and synthetic labels reconcile',()=>{
 const byId=new Map(gold.map(x=>[x.activity_id,x]));
 assert.equal(predicted.length,gold.filter(x=>x.is_positive).length);
 for(const p of predicted){
  const g=byId.get(p.activity_id);
  assert.ok(g?.is_positive);
  assert.equal(p.actor_contact_id,g.actor_contact_id);
  assert.equal(p.target_contact_id,g.target_contact_id);
  assert.equal(p.relation_type,g.relation_type);
  assert.equal(p.evidence_text,g.evidence_text);
  assert.equal(p.influence_verified,false);
 }
});
test('negative examples excluded',()=>{
 const negatives=new Set(gold.filter(x=>!x.is_positive).map(x=>x.activity_id));
 assert.ok(negatives.size>0);
 assert.ok(predicted.every(x=>!negatives.has(x.activity_id)));
});
