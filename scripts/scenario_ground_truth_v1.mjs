import {isDeepStrictEqual} from "node:util";
import {createHash} from "node:crypto";
import {validate as validateWorld} from "./scenario_engine_v4.mjs";
import {validateCommunications} from "./scenario_communication_generator_v1.mjs";

export function buildGroundTruth(dataset) {
  const w=dataset.world;
  for(const result of [validateWorld(w),validateCommunications(dataset)]) {
    if(!result.pass) throw Error(result.errors.join("; "));
  }
  const activities=new Map(dataset.communications.map(a=>[a.SOURCE_EVENT_ID,a]));
  const initiators=new Map(w.events.filter(e=>e.type==="request_information").map(e=>[e.deal_id,e.actor_id]));
  const records=w.events.map(e=>{
    const a=activities.get(e.id);
    const decision=["approve","reject"].includes(e.type);
    const execution=["complete_task","revise"].includes(e.type);
    const participants=[...new Set([e.actor_id,...(e.target_id?[e.target_id]:[])])];
    if(!isDeepStrictEqual(a.COMMUNICATIONS,participants)||a.ORGANIZATION_ID!==e.org||a.EVENT_TYPE!==e.type||a.PREVIOUS_EVENT_ID!==e.previous_event_id) throw Error("source projection mismatch "+e.id);
    if(!initiators.has(e.deal_id)) throw Error("missing initiator "+e.id);
    return {
      event_id:e.id,scenario_instance_id:e.deal_id,process_instance_id:null,
      organization_id:e.org,deal_id:e.deal_id,occurred_at:e.occurred_at,previous_event_id:e.previous_event_id,
      event_type:e.type,relation_type:e.category,decision_scope:e.scope,
      initiator_contact_id:initiators.get(e.deal_id),actor_contact_id:e.actor_id,
      speaker_contact_id:null,document_author_contact_id:a.AUTHOR_ID,
      participant_contact_ids:participants,target_contact_id:e.target_id,
      addressee_contact_ids:e.target_id?[e.target_id]:[],
      executor_contact_id:execution?e.actor_id:null,
      decision_maker_contact_id:decision?e.actor_id:null,
      decision_outcome:decision?e.type:null,
      authority_grant_refs:decision?w.grants.filter(g=>g.person_id===e.actor_id&&g.org===e.org&&g.scope===e.scope&&e.occurred_at.slice(0,10)>=g.valid_from&&(!g.valid_to||e.occurred_at.slice(0,10)<g.valid_to)).map(g=>({...g})):[],
      attribution_status:"synthetic_by_construction",speaker_status:"unknown_no_turn_annotation",
      target_status:e.target_id?"synthetic_by_construction":"not_specified",
      executor_status:execution?"synthetic_by_construction":"not_applicable",
      decision_status:decision?"synthetic_by_construction":"not_applicable",
      evidence_refs:[{activity_id:a.ID,source_type:a.CHANNEL,source_event_id:e.id,
        text_sha256:createHash("sha256").update(a.DESCRIPTION,"utf8").digest("hex"),span_status:"not_annotated"}],
      annotation_origin:"scenario_engine_v4"
    };
  });
  return {schema_version:"0.1.0",seed:dataset.seed,synthetic:true,visibility:"evaluation_only",source:"scenario_engine_v4",records};
}
export function validateGroundTruth(dataset,gold){
  try {const expected=buildGroundTruth(dataset);return {pass:isDeepStrictEqual(expected,gold),errors:isDeepStrictEqual(expected,gold)?[]:["gold differs from source projection"]};}
  catch(e){return {pass:false,errors:[e.message]};}
}
