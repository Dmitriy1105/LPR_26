import assert from "node:assert/strict";
import {generateCommunications} from "./scenario_communication_generator_v1.mjs";
const seeds=[42,7,19,2026,99173];
function metrics(seed){
 const d=generateCommunications({seed});
 const groups=new Map();
 for(const a of d.communications){
  const body=a.DESCRIPTION.split(" Сделка: ")[0].trim();
  const subject=a.SUBJECT.replace(/ ORG-\\d+-D\\d+$/,"").trim();
  if(!groups.has(a.EVENT_TYPE))groups.set(a.EVENT_TYPE,{bodies:new Set(),subjects:new Set(),count:0});
  const g=groups.get(a.EVENT_TYPE);g.count++;g.bodies.add(body);g.subjects.add(subject);
 }
 const rows=[...groups.entries()].sort(([a],[b])=>a.localeCompare(b)).map(([event_type,g])=>({
  event_type,communications:g.count,unique_body_variants:g.bodies.size,unique_subject_variants:g.subjects.size
 }));
 return {dataset:d,rows,uniqueBodies:rows.reduce((n,x)=>n+x.unique_body_variants,0)};
}
const results=seeds.map(seed=>({seed,...metrics(seed)}));
for(const x of results){
 assert.equal(x.dataset.communications.length,x.dataset.event_count);
 assert.equal(x.rows.length,10);
 assert.ok(x.uniqueBodies>=40,"insufficient unique body variants for seed "+x.seed+": "+x.uniqueBodies);
 assert.ok(x.rows.every(r=>r.unique_body_variants>=3),"event type has fewer than 3 variants for seed "+x.seed);
 assert.ok(x.dataset.communications.every(a=>!/(decision_maker_contact_id|authority_grant_refs|ground.?truth)/i.test(a.DESCRIPTION)),"gold metadata leaked into text");
 const replay=generateCommunications({seed:x.seed});
 assert.deepEqual(replay.communications,x.dataset.communications,"non-deterministic replay for seed "+x.seed);
}
const tokenSet=s=>new Set(s.toLowerCase().replace(/[^\\p{L}\\p{N}]+/gu," ").split(/\\s+/).filter(Boolean));
const jaccard=(a,b)=>{const A=tokenSet(a),B=tokenSet(b);let n=0;for(const t of A)if(B.has(t))n++;return n/(A.size+B.size-n||1)};
let maxSimilarity=0,highSimilarityPairs=0;
for(const x of results){
 const messages=x.dataset.communications.map(a=>({type:a.EVENT_TYPE,body:a.DESCRIPTION.split(" Сделка: ")[0].trim()}));
 for(let i=0;i<messages.length;i++)for(let j=i+1;j<messages.length;j++){
  if(messages[i].type!==messages[j].type)continue;
  const s=jaccard(messages[i].body,messages[j].body);
  maxSimilarity=Math.max(maxSimilarity,s);
  if(s>=0.85)highSimilarityPairs++;
 }
}
const report={
 status:"PASS",seeds:results.map(x=>x.seed),communications_per_seed:results.map(x=>x.dataset.communications.length),
 unique_body_variants_per_seed:results.map(x=>x.uniqueBodies),
 event_type_metrics:results.map(x=>({seed:x.seed,metrics:x.rows})),
 max_within_type_jaccard:maxSimilarity,high_similarity_pairs:highSimilarityPairs,
 deterministic_replay:true,gold_label_leakage:false,
 method:"exact normalized text diversity + token Jaccard; does not establish semantic realism or dialogue quality"
};
console.log(JSON.stringify(report,null,2));
