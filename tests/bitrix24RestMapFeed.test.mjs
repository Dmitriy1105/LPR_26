import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {buildRestMapFeed} from '../src/integrations/bitrix24/buildRestMapFeed.mjs';
const read=p=>JSON.parse(readFileSync(new URL('../src/data/bitrix24_contract_v1/'+p,import.meta.url),'utf8'));
const contacts=read('contacts/page_001.json');
const pages=Array.from({length:11},(_,i)=>read('activities/page_'+String(i+1).padStart(3,'0')+'.json'));
const calls=read('nlp/call_transcript_responses.json');
test('map feed derives 30 people and 540 interactions from REST JSON alone',()=>{
 const feed=buildRestMapFeed(contacts,pages,calls);
 assert.equal(feed.people.length,30);
 assert.equal(feed.interactions.length,540);
 assert.ok(feed.interactions.every(x=>x.source==='bitrix24_rest'&&x.textSource));
 assert.ok(feed.people.every(p=>p.decisionRole===null&&p.influence===null&&p.stance===null));
});
test('map feed rejects dangling REST contact references',()=>{
 const altered=structuredClone(pages);
 altered[0].result[0].OWNER_ID='999999';
 assert.throws(()=>buildRestMapFeed(contacts,altered,calls),/Unknown REST contact/);
});
