import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read = path => JSON.parse(readFileSync(new URL(path, import.meta.url),'utf8'));
const base='../src/data/bitrix24_contract_v1/';
const activities=Array.from({length:11},(_,i)=>read(base+'activities/page_'+String(i+1).padStart(3,'0')+'.json').result).flat();
const contacts=read(base+'contacts/page_001.json').result.items;
const deals=read(base+'deals/page_001.json').result.items;
const calls=read(base+'nlp/call_transcript_responses.json').responses;
const emails=read(base+'nlp/email_content_responses.json').responses;
const ids=new Set(contacts.map(x=>String(x.id)));
test('contacts have separate names and all CRM activities point to known contacts',()=>{
 assert.equal(contacts.length,30);
 for(const c of contacts){assert.ok(c.name&&c.lastName);assert.notEqual(c.name,c.lastName)}
 for(const a of activities) assert.ok(ids.has(a.OWNER_ID),'activity '+a.ID);
 for(const d of deals) for(const c of d.contactIds) assert.ok(ids.has(String(c)));
});
test('all 180 call transcripts are extractable from REST-like JSON',()=>{
 const a=activities.filter(x=>x.TYPE_ID==='2');
 assert.equal(a.length,180);assert.equal(Object.keys(calls).length,a.length);
 for(const x of a) assert.ok(calls[x.ID]?.result?.transcription?.length>60,x.ID);
});
test('all 270 email texts match CRM REST DESCRIPTION exactly',()=>{
 const a=activities.filter(x=>x.TYPE_ID==='4');
 assert.equal(a.length,270);assert.equal(Object.keys(emails).length,a.length);
 for(const x of a){
   assert.ok(x.DESCRIPTION.length>280,x.ID);
   assert.equal(emails[x.ID]?.result?.body,x.DESCRIPTION);
 }
});
test('all meeting descriptions are nonempty and activity IDs are unique',()=>{
 assert.equal(activities.length,540);
 assert.equal(new Set(activities.map(x=>x.ID)).size,540);
 const meetings=activities.filter(x=>x.TYPE_ID==='1');
 assert.equal(meetings.length,90);
 for(const x of meetings)assert.ok(x.DESCRIPTION.length>200,x.ID);
});
