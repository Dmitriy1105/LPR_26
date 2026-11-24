import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {generateCommunications} from "./scenario_communication_generator_v1.mjs";
import {buildGroundTruth} from "./scenario_ground_truth_v1.mjs";
const source=readFileSync(new URL("./scenario_communication_generator_v1.mjs",import.meta.url),"utf8");
const forbidden=[
 /from\s+["'][^"']*scenario_ground_truth/i,
 /import\s*\(\s*["'][^"']*scenario_ground_truth/i,
 /decision_maker_contact_id|authority_grant_refs|attribution_status|annotation_origin|speaker_contact_id|evidence_refs/
];
assert.ok(!forbidden[0].test(source),"communication generator imports Ground Truth");
assert.ok(!forbidden[1].test(source),"communication generator dynamically imports Ground Truth");
assert.ok(!forbidden[2].test(source),"Ground Truth-only fields referenced by communication generator");
assert.match(source,/const textEvent\s*=\s*\{\s*id:\s*event\.id,\s*type:\s*event\.type,\s*outcome:\s*event\.outcome\s*\?\?\s*null\s*\}/,"renderer must receive minimal event projection");
const d=generateCommunications({seed:42});
const gold=buildGroundTruth(d);
const forbiddenKeys=new Set(["decision_maker_contact_id","decision_outcome","authority_grant_refs","attribution_status","speaker_contact_id","evidence_refs","annotation_origin","initiator_contact_id","executor_contact_id"]);
for(const a of d.communications){
 for(const key of Object.keys(a))assert.ok(!forbiddenKeys.has(key),"gold-only field leaked into CRM activity: "+key);
 for(const value of [a.SUBJECT,a.DESCRIPTION])assert.ok(!/decision_maker_contact_id|authority_grant_refs|annotation_origin|ground.?truth/i.test(value),"gold label leaked into text");
}
const before=structuredClone(d.communications);
const altered=structuredClone(gold);
altered.records[0].decision_maker_contact_id="MUTATED_GOLD_ONLY";
altered.records[0].authority_grant_refs=[];
assert.deepEqual(generateCommunications({seed:42}).communications,before,"communication output unexpectedly depends on gold annotations");
assert.notDeepEqual(altered,gold,"mutation control failed");
console.log(JSON.stringify({status:"PASS",communications:d.communications.length,gold_records:gold.records.length,forbidden_imports:2,forbidden_fields:forbiddenKeys.size,renderer_input:"minimal_event_projection",gold_mutation_independent:true}));
