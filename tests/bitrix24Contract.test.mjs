import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {generateFixtures} from '../scripts/generate_bitrix24_contract_fixtures.mjs';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const data=generateFixtures(read('../src/data/crm.json'),read('../src/data/synthetic/bank_ml_v2.json'));
test('deterministic generated REST fixtures including enriched texts',()=>{
 for(const [p,v] of [['manifest.json',data.manifest],['id_mapping.json',data.mapping],...Object.entries(data.pages),...Object.entries(data.errors).map(([k,v])=>['errors/'+k+'.json',v])]){
  const actual=read('../src/data/bitrix24_contract_v1/'+p);
  const normalize=x=>JSON.parse(JSON.stringify(x));
  assert.deepEqual(normalize(actual),normalize(v),p);
 }
});
test('complete pagination with correct envelope and cursor',()=>{for(const m of data.manifest.methods){let n=0;for(let i=0;i<m.pages.length;i++){const p=m.pages[i],r=data.pages[p.file],items=m.resultPath==='result.items'?r.result.items:m.resultPath==='result.tasks'?r.result.tasks:r.result;assert.equal(items.length,p.count);assert.ok(items.length<=50);assert.equal(r.total,m.recordCount);assert.equal(r.next,i+1<m.pages.length?(i+1)*50:undefined);n+=items.length;}assert.equal(n,m.recordCount);}});
test('CRM references are consistent',()=>{const ids=new Set(Object.values(data.mapping.contactIds));const deals=new Set(Object.values(data.mapping.dealIds));for(const d of data.pages['deals/page_001.json'].result.items)for(const c of d.contactIds)assert.ok(ids.has(c));for(const [p,r] of Object.entries(data.pages))if(p.startsWith('activities/'))for(const a of r.result){assert.ok(ids.has(Number(a.OWNER_ID)));assert.ok(a.END_TIME>=a.START_TIME)}for(const t of data.pages['tasks/page_001.json'].result.tasks)for(const ref of t.ufCrmTask){const [type,id]=ref.split('_');assert.ok(type==='C'?ids.has(Number(id)):type==='D'&&deals.has(Number(id)));}});
test('manual fields are not included in REST objects',()=>{for(const p of Object.values(data.pages))for(const k of ['manualAnnotations','decisionRole','influence','warmth','stance','relationshipEvents','synthetic'])assert.equal(JSON.stringify(p).includes('"'+k+'"'),false)});
