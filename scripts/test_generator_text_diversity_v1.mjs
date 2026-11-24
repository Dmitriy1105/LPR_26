import assert from "node:assert/strict";
import {generateCommunications} from "./scenario_communication_generator_v1.mjs";
const data=generateCommunications({seed:42});
const groups=new Map();
for(const a of data.communications){
 const body=a.DESCRIPTION.split(" Сделка: ")[0].trim();
 const subject=a.SUBJECT.replace(/ ORG-\\d+-D\\d+$/,"").trim();
 const key=a.EVENT_TYPE;
 if(!groups.has(key))groups.set(key,{bodies:new Set(),subjects:new Set(),count:0});
 const g=groups.get(key);g.count++;g.bodies.add(body);g.subjects.add(subject);
}
const tokenSet=s=>new Set(s.toLowerCase().replace(/[^\\p{L}\\p{N}]+/gu," ").split(/\\s+/).filter(Boolean));
const jaccard=(a,b)=>{const A=tokenSet(a),B=tokenSet(b);let n=0;for(const t of A)if(B.has(t))n++;return n/(A.size+B.size-n||1)};
const all=[...groups.entries()].flatMap(([type,g])=>[...g.bodies].map(text=>({type,text})));
let maxSimilarity=0,highSimilarityPairs=0;
for(let i=0;i<all.length;i++)for(let j=i+1;j<all.length;j++){if(all[i].type!==all[j].type)continue;const s=jaccard(all[i].text,all[j].text);maxSimilarity=Math.max(maxSimilarity,s);if(s>=0.85)highSimilarityPairs++;}
const metrics=[...groups.entries()].sort(([a],[b])=>a.localeCompare(b)).map(([event_type,g])=>({event_type,communications:g.count,unique_body_templates:g.bodies.size,unique_subject_templates:g.subjects.size,body_template_coverage:g.bodies.size/Math.max(1,g.count)}));
const totalUnique=all.length,allMessages=data.communications.length;
const report={status:"PASS",seed:42,total_communications:allMessages,event_types:metrics.length,unique_body_templates:totalUnique,body_template_ratio:totalUnique/allMessages,metrics,max_within_type_jaccard:maxSimilarity,high_similarity_pairs:highSimilarityPairs,method:"exact normalized template diversity + token Jaccard; not semantic realism validation"};
assert.equal(allMessages,data.event_count);
assert.equal(metrics.length,10);
assert.ok(totalUnique>=15,"fewer than 15 distinct normalized body templates");
assert.ok(metrics.every(x=>x.unique_body_templates>=2),"an event type has fewer than two body variants");
assert.ok(data.communications.every(x=>!/(decision_maker_contact_id|authority_grant_refs|ground.?truth)/i.test(x.DESCRIPTION)),"hidden gold metadata leaked into text");
console.log(JSON.stringify(report,null,2));
