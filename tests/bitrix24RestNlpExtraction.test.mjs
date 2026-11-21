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
