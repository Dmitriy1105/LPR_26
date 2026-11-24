// Synthetic world-state engine; no CRM text rendering or NLP inference.
export const VERSION = "4.0.0-alpha.1";
export const taxonomy = Object.freeze({
 request_information:"communication", recommend:"influence", object:"opposition",
 delegate:"management", complete_task:"execution", review:"expertise",
 approve:"authority", reject:"authority", revise:"execution", close:"workflow"
});
const roles = [
 ["director","executive",["commercial","budget","technical"]],
 ["finance_head","finance",["budget"]],
 ["technical_head","IT",["technical"]],
 ["procurement_head","procurement",["commercial"]],
 ["analyst","IT",[]],["buyer","procurement",[]]
];
function rng(seed){let s=seed>>>0;return ()=>{s=(Math.imul(1664525,s)+1013904223)>>>0;return s/4294967296;};}
export function generate({seed=42,organizations=5,dealsPerOrganization=6}={}){
 if(!Number.isInteger(seed)||!Number.isInteger(organizations)||organizations<1||!Number.isInteger(dealsPerOrganization)||dealsPerOrganization<1)throw Error("invalid configuration");
 const random=rng(seed), people=[],orgs=[],deals=[],events=[],grants=[];
 for(let o=0;o<organizations;o++){
  const org="ORG-"+(o+1);orgs.push({id:org});
  const staff=roles.map(([role,department,scopes],i)=>{
   const id=org+"-P"+(i+1);const p={id,org,role,department};people.push(p);
   for(const scope of scopes)grants.push({person_id:id,org,scope,valid_from:"2026-01-01",valid_to:null});
   return p;
  });
  for(let d=0;d<dealsPerOrganization;d++){
   const id=org+"-D"+(d+1), scope=["technical","budget","commercial"][Math.floor(random()*3)];
   const owner=staff[scope==="technical"?2:scope==="budget"?1:3], expert=staff[4],buyer=staff[5];
   const approver=random()<.25?staff[0]:owner;
   const scenario=random(), family=scenario<.4?"routine":scenario<.8?"revision":"rejected";
   const deal={id,org,scope,family,status:"open"};deals.push(deal);
   let clock=Date.UTC(2026,1,1+d*5),previous=null;
   function emit(type,actor,target=null,extra={}){
    clock+=(1+Math.floor(random()*24))*3600000;
    const event={id:id+"-E"+(events.length+1),deal_id:id,org,scope,type,category:taxonomy[type],actor_id:actor.id,target_id:target?.id??null,occurred_at:new Date(clock).toISOString(),previous_event_id:previous, ...extra};
    events.push(event);previous=event.id;return event;
   }
   emit("request_information",buyer,owner);
   emit("delegate",owner,expert);
   emit("complete_task",expert,owner);
   emit("review",owner,expert);
   emit("recommend",expert,approver);
   if(family==="revision"){emit("object",approver,approver.id===owner.id?expert:owner);emit("revise",expert,owner);emit("review",owner,expert);}
   emit(family==="rejected"?"reject":"approve",approver);
   deal.status=family==="rejected"?"rejected":"approved";
   emit("close",owner,null,{outcome:deal.status});
  }
 }
 return {version:VERSION,seed,organizations:orgs,people,grants,deals,events};
}
export function validate(w){
 const errors=[],check=(ok,msg)=>{if(!ok)errors.push(msg);};
 const people=new Map(w.people.map(p=>[p.id,p])), deals=new Map(w.deals.map(d=>[d.id,d])), seen=new Set();
 for(const a of [w.organizations,w.people,w.deals,w.events])check(new Set(a.map(x=>x.id)).size===a.length,"duplicate id");
 for(const d of w.deals){
  const es=w.events.filter(e=>e.deal_id===d.id);let prev=null,decision=null;
  for(const e of es){
   check(!!taxonomy[e.type],"unknown type "+e.id);
   check(e.org===d.org&&e.scope===d.scope,"scope mismatch "+e.id);
   check(people.get(e.actor_id)?.org===d.org,"actor mismatch "+e.id);
   check(e.target_id===null||people.get(e.target_id)?.org===d.org,"target mismatch "+e.id);
   check(e.type!=="object"||e.actor_id!==e.target_id,"self-directed objection "+e.id);
   check(e.previous_event_id===(prev?.id??null),"broken chronology "+e.id);
   check(Number.isFinite(Date.parse(e.occurred_at))&&(!prev||Date.parse(e.occurred_at)>Date.parse(prev.occurred_at)),"invalid time "+e.id);
   if(["approve","reject"].includes(e.type)){
    check(!decision,"multiple decisions "+e.id);
    check(w.grants.some(g=>g.person_id===e.actor_id&&g.org===e.org&&g.scope===e.scope&&e.occurred_at.slice(0,10)>=g.valid_from&&(!g.valid_to||e.occurred_at.slice(0,10)<g.valid_to)),"unauthorized decision "+e.id);
    check(prev?.type==="review"||prev?.type==="recommend","decision without review "+e.id);
    decision=e.type;
   }
   if(e.type==="close")check(!!decision&&e.outcome===d.status&&d.status===(decision==="approve"?"approved":"rejected"),"invalid closure "+e.id);
   seen.add(e.id);prev=e;
  }
  check(prev?.type==="close","missing closure "+d.id);
 }
 check(seen.size===w.events.length&&w.events.every(e=>deals.has(e.deal_id)),"orphan event");
 return {pass:errors.length===0,errors};
}
