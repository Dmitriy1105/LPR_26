import assert from "node:assert/strict";
import {generateCommunications} from "./scenario_communication_generator_v1.mjs";
import {buildGroundTruth,validateGroundTruth} from "./scenario_ground_truth_v1.mjs";
export function audit(d,g){
 const w=d.world, errors=[], check=(ok,msg)=>{if(!ok)errors.push(msg)};
 const index=(rows,key)=>{const m=new Map(rows.map(r=>[r[key],r]));check(m.size===rows.length,"duplicate "+key);return m};
 const org=index(w.organizations,"id"),people=index(w.people,"id"),deals=index(w.deals,"id"),events=index(w.events,"id"),acts=index(d.communications,"ID"),gold=index(g.records,"event_id");
 for(const p of w.people)check(org.has(p.org),"person organization "+p.id);
 for(const x of w.deals)check(org.has(x.org),"deal organization "+x.id);
 for(const x of w.grants)check(people.get(x.person_id)?.org===x.org&&org.has(x.org),"grant organization "+x.person_id);
 const last=new Map();
 for(const e of w.events){
  const prev=last.get(e.deal_id);
  check(org.has(e.org)&&deals.get(e.deal_id)?.org===e.org,"event deal "+e.id);
  check(people.get(e.actor_id)?.org===e.org,"actor "+e.id);
  check(e.target_id===null||people.get(e.target_id)?.org===e.org,"target "+e.id);
  check(e.previous_event_id===(prev?.id??null),"previous "+e.id);
  check(Number.isFinite(Date.parse(e.occurred_at))&&(!prev||Date.parse(e.occurred_at)>Date.parse(prev.occurred_at)),"chronology "+e.id);
  last.set(e.deal_id,e);
 }
 const linked=new Set();
 for(const a of d.communications){
  const e=events.get(a.SOURCE_EVENT_ID);
  check(!!e&&!linked.has(a.SOURCE_EVENT_ID),"activity event "+a.ID);linked.add(a.SOURCE_EVENT_ID);
  check(a.DEAL_ID===e?.deal_id&&a.OWNER_ID===e?.deal_id&&a.ORGANIZATION_ID===e?.org,"activity owner "+a.ID);
  check(a.CREATED===e?.occurred_at,"activity time "+a.ID);
  check(Array.isArray(a.COMMUNICATIONS)&&new Set(a.COMMUNICATIONS).size===a.COMMUNICATIONS.length&&a.COMMUNICATIONS.every(p=>people.get(p)?.org===e?.org),"participants "+a.ID);
 }
 for(const r of g.records){
  const e=events.get(r.event_id);
  check(!!e&&r.deal_id===e?.deal_id&&r.organization_id===e?.org&&r.occurred_at===e?.occurred_at,"gold event "+r.event_id);
  for(const ref of r.evidence_refs)check(acts.get(ref.activity_id)?.SOURCE_EVENT_ID===r.event_id,"gold evidence "+r.event_id);
 }
 check(linked.size===events.size&&gold.size===events.size,"coverage");
 check(validateGroundTruth(d,g).pass,"ground truth projection");
 return {pass:errors.length===0,errors,events:events.size,activities:acts.size,gold:gold.size};
}
const seeds=[0,1,42,20261124,4294967295],results=[];
for(const seed of seeds){const d=generateCommunications({seed}),g=buildGroundTruth(d),r=audit(d,g);assert.ok(r.pass,JSON.stringify(r.errors));results.push({seed,...r});}
const d=generateCommunications(),g=buildGroundTruth(d);
const mutations=[
 (d,g)=>d.world.people[0].org="missing",
 (d,g)=>d.world.deals[0].org="missing",
 (d,g)=>d.world.events[1].previous_event_id=null,
 (d,g)=>d.world.events[1].occurred_at=d.world.events[0].occurred_at,
 (d,g)=>d.communications[0].OWNER_ID="missing",
 (d,g)=>d.communications[0].COMMUNICATIONS.push(d.communications[0].COMMUNICATIONS[0]),
 (d,g)=>g.records[0].evidence_refs[0].activity_id="missing",
 (d,g)=>d.communications[0].CREATED="invalid"
];
for(const mutate of mutations){const x=structuredClone(d),y=structuredClone(g);mutate(x,y);assert.equal(audit(x,y).pass,false);}
console.log(JSON.stringify({status:"PASS",results,negative_cases:mutations.length,scope:"scenario_projection_not_bpmn_trace"}));
