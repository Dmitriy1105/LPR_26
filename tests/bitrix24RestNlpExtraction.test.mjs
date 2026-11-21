import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {extractRestNlpDocuments} from '../src/integrations/bitrix24/extractRestNlpDocuments.mjs';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const root='../src/data/bitrix24_contract_v1/';
const pages=Array.from({length:11},(_,i)=>read(root+'activities/page_'+String(i+1).padStart(3,'0')+'.json'));
const transcripts=read(root+'nlp/call_transcript_responses.json');
test('REST JSON alone yields 540 NLP documents with correct types',()=>{
 const docs=extractRestNlpDocuments(pages,transcripts);
 assert.equal(docs.length,540);
 assert.equal(docs.filter(d=>d.activityType==='call').length,180);
 assert.equal(docs.filter(d=>d.activityType==='email').length,270);
 assert.equal(docs.filter(d=>d.activityType==='meeting').length,90);
 assert.equal(docs.filter(d=>d.status==='ready').length,540);
 for(const d of docs){assert.ok(d.text.length>60);assert.ok(d.contactId);assert.ok(d.activityId)}
});
test('missing transcript is represented as missing, not generated',()=>{
 const id=pages.flatMap(p=>p.result).find(a=>a.TYPE_ID==='2').ID;
 const altered={responses:{...transcripts.responses,[id]:{result:null}}};
 const docs=extractRestNlpDocuments(pages,altered);
 const call=docs.find(d=>d.activityId===id);
 assert.equal(call.status,'missing_text');assert.equal(call.text,null);
});
test('duplicate activity IDs fail loudly',()=>{
 assert.throws(()=>extractRestNlpDocuments([pages[0],pages[0]],transcripts),/Duplicate/);
});

test('REST negative scenarios represent missing or inaccessible text without fabrication',()=>{
 const scenarios=read(root+'nlp/missing_text_scenarios.json');
 for(const item of scenarios.cases){
  const copy=structuredClone(pages);
  const altered=structuredClone(transcripts);
  const activity=copy.flatMap(p=>p.result).find(a=>item.activityId?a.ID===item.activityId:a.TYPE_ID===item.selector?.TYPE_ID);
  assert.ok(activity,item.id);
  if(item.method==='crm.activity.call.getTranscript')altered.responses[activity.ID]=item.response;
  else Object.assign(activity,item.override);
  const doc=extractRestNlpDocuments(copy,altered).find(d=>d.activityId===activity.ID);
  assert.equal(doc.status,item.expectedStatus,item.id);
  assert.equal(doc.text,null,item.id);
 }
});
