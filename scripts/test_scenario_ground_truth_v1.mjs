import assert from "node:assert/strict";
import {generateCommunications} from "./scenario_communication_generator_v1.mjs";
import {buildGroundTruth,validateGroundTruth} from "./scenario_ground_truth_v1.mjs";
const d=generateCommunications(),g=buildGroundTruth(d);
assert.equal(g.records.length,d.world.events.length);
assert.deepEqual(g,buildGroundTruth(generateCommunications()));
assert.equal(validateGroundTruth(d,g).pass,true);
assert.equal(new Set(g.records.map(r=>r.event_id)).size,g.records.length);
assert.ok(g.records.every(r=>r.speaker_contact_id===null&&r.process_instance_id===null));
assert.ok(g.records.filter(r=>r.decision_maker_contact_id!==null).every(r=>r.authority_grant_refs.length>0));
assert.ok(g.records.some(r=>r.target_contact_id===null&&r.addressee_contact_ids.length===0));
assert.ok(d.communications.every(a=>!("decision_maker_contact_id" in a)&&!("annotation_origin" in a)));
const mutations=[
 x=>x.records[0].actor_contact_id="UNKNOWN",
 x=>x.records[0].speaker_contact_id=x.records[0].actor_contact_id,
 x=>x.records[0].previous_event_id="bad",
 x=>x.records[0].evidence_refs[0].text_sha256="bad",
 x=>x.records.pop(),
 x=>x.records.push(x.records[0]),
 x=>x.records.find(r=>r.decision_maker_contact_id).authority_grant_refs=[],
 x=>x.records[0].process_instance_id="invented"
];
for(const mutate of mutations){const x=structuredClone(g);mutate(x);assert.equal(validateGroundTruth(d,x).pass,false);}
console.log(JSON.stringify({status:"PASS",records:g.records.length,decisions:g.records.filter(r=>r.decision_maker_contact_id).length,negative_cases:mutations.length,deterministic:true,scope:"scenario_projection_only"}));
