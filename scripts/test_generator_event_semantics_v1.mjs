import assert from "node:assert/strict";
import {generateCommunications} from "./scenario_communication_generator_v1.mjs";
import {buildGroundTruth} from "./scenario_ground_truth_v1.mjs";
const expected={
 request_information:[4,"email","communication"],delegate:[4,"email","management"],
 complete_task:[2,"call","execution"],review:[1,"meeting","expertise"],
 recommend:[4,"email","influence"],object:[4,"email","opposition"],
 revise:[2,"call","execution"],approve:[1,"meeting","authority"],
 reject:[1,"meeting","authority"],close:[1,"meeting","workflow"]
};
function audit(d,g){
 const errors=[],check=(ok,msg)=>{if(!ok)errors.push(msg)};
 const a=new Map(d.communications.map(x=>[x.SOURCE_EVENT_ID,x])),r=new Map(g.records.map(x=>[x.event_id,x]));
 for(const e of d.world.events){
  const c=a.get(e.id),t=r.get(e.id),spec=expected[e.type];
  if(!c||!t||!spec){errors.push("missing projection "+e.id);continue;}
  const decision=e.type==="approve"||e.type==="reject",execution=e.type==="complete_task"||e.type==="revise";
  check(c.TYPE_ID===spec[0]&&c.CHANNEL===spec[1]&&c.EVENT_TYPE===e.type,"channel "+e.id);
  check(t.event_type===e.type&&t.relation_type===spec[2],"taxonomy "+e.id);
  check(t.actor_contact_id===e.actor_id&&t.target_contact_id===e.target_id,"actor/target "+e.id);
  check(t.decision_maker_contact_id===(decision?e.actor_id:null)&&t.decision_outcome===(decision?e.type:null),"decision "+e.id);
  check(t.executor_contact_id===(execution?e.actor_id:null),"executor "+e.id);
  check(t.speaker_contact_id===null&&t.process_instance_id===null,"unsupported attribution "+e.id);
  check(t.document_author_contact_id===c.AUTHOR_ID&&c.AUTHOR_ID===e.actor_id,"author "+e.id);
  check(t.evidence_refs.length===1&&t.evidence_refs[0].activity_id===c.ID&&t.evidence_refs[0].source_type===c.CHANNEL,"evidence "+e.id);
 }
 return errors;
}
const d=generateCommunications(),g=buildGroundTruth(d);
assert.deepEqual(audit(d,g),[]);
assert.deepEqual([...new Set(d.world.events.map(e=>e.type))].sort(),Object.keys(expected).sort());
const mutations=[
 (d,g)=>d.communications[0].TYPE_ID=1,
 (d,g)=>g.records.find(x=>x.event_type==="recommend").decision_maker_contact_id="invented",
 (d,g)=>g.records.find(x=>x.event_type==="object").relation_type="authority",
 (d,g)=>g.records.find(x=>x.event_type==="delegate").executor_contact_id="invented",
 (d,g)=>g.records[0].speaker_contact_id=g.records[0].actor_contact_id,
 (d,g)=>g.records[0].evidence_refs[0].source_type="meeting"
];
for(const mutate of mutations){const x=structuredClone(d),y=structuredClone(g);mutate(x,y);assert.ok(audit(x,y).length);}
console.log(JSON.stringify({status:"PASS",events:d.world.events.length,event_types:Object.keys(expected).length,negative_cases:mutations.length,scope:"structured_semantics_only",text_entailment_verified:false,bpmn_trace_verified:false}));
