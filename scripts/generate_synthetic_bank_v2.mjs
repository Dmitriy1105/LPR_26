// Deterministic fictional data for bank contacts already in src/data/crm.json.
// Run: node scripts/generate_synthetic_bank_v2.mjs
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
export function generateV2(crm,v1,seed=20261121){
 const companyId="bank",asOf="2026-11-21",people=crm.people.filter(p=>p.companyId===companyId);
 if(people.length!==30||v1.metadata.companyId!=="bank")throw Error("Invalid source");
 let state=seed>>>0;
 const rand=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return(state>>>0)/4294967296};
 const int=(a,b)=>a+Math.floor(rand()*(b-a+1)),pick=a=>a[int(0,a.length-1)];
 const date=(d,n)=>{const x=new Date(d+"T12:00:00Z");x.setUTCDate(x.getUTCDate()+n);return x.toISOString().slice(0,10)};
 const days=(a,b)=>Math.round((Date.parse(b+"T00:00:00Z")-Date.parse(a+"T00:00:00Z"))/86400000);
 const group=k=>people.filter(p=>p.department===k),decision=people.filter(p=>p.decisionRole==="decision_maker");
 const it=group("ИТ"),sec=group("ИБ"),fin=group("Финансы"),buy=group("Закупки"),business=group("Бизнес");
 const idSet=new Set(people.map(p=>p.id)),byId=new Map(people.map(p=>[p.id,p]));
 const opportunities=[...v1.opportunities],stages=["lost","lost","lost","lost","stalled","stalled","negotiating","negotiating"];
 for(let i=0;i<8;i++){
  const createdDate=date("2025-04-15",i*65+int(0,16)),stage=stages[i],leader=decision[(i+2)%decision.length];
  opportunities.push({id:`opp-bank-extra-${i+1}`,companyId,primaryPersonId:leader.id,stakeholderIds:[leader.id,buy[i%buy.length].id,fin[i%fin.length].id,sec[i%sec.length].id],manager:leader.owner,createdDate,stage,closedDate:stage==="lost"?date(createdDate,80+int(0,65)):null,estimatedAmountRub:int(18,140)*100000,synthetic:true});
 }
 const approvalSteps=[],decisionMeetings=[],clientInternalMessages=[],referrals=[],competitorMentions=[],decisionOutcomes=[];
 const steps=[["technical",it],["security",sec],["budget",fin],["procurement",buy],["final",decision]];
 for(let i=0;i<opportunities.length;i++){
  const opp=opportunities[i],span=Math.max(10,days(opp.createdDate,opp.closedDate||asOf));
  const rejectIndex=opp.stage==="lost"?(i%2===0?1:2):opp.stage==="stalled"?2:3;
  const stepIds=[];
  for(let k=0;k<steps.length;k++){
   const person=steps[k][1][(i+k)%steps[k][1].length],d=date(opp.createdDate,Math.floor(span*(k+1)/7));
   const status=opp.stage==="won"?"approved":opp.stage==="lost"?(k<rejectIndex?"approved":k===rejectIndex?"rejected":"not_started"):(k<rejectIndex?"approved":"pending");
   const id=`approval-${opp.id}-${k+1}`;stepIds.push(id);
   approvalSteps.push({id,companyId,opportunityId:opp.id,personId:person.id,date:d,stage:steps[k][0],status,reason:status==="rejected"?"Не согласованы ключевые условия":status==="pending"?"Ожидается решение":status==="approved"?"Этап согласован":"Этап ещё не начат",synthetic:true});
  }
  for(let k=0;k<2;k++){
   const d=date(opp.createdDate,Math.floor(span*(k+2)/5));
   decisionMeetings.push({id:`decision-meeting-${opp.id}-${k+1}`,companyId,opportunityId:opp.id,date:d,clientAttendeeIds:[...new Set([opp.primaryPersonId,opp.stakeholderIds[k+1]])],ourAttendees:[opp.manager],agenda:k===0?"Технические требования":"Бюджет и выбор поставщика",minutes:opp.stage==="won"?"Подтверждены условия и дальнейшие шаги.":opp.stage==="lost"?"Выявлены существенные возражения.":"Требуются дополнительные согласования.",synthetic:true});
   clientInternalMessages.push({id:`internal-${opp.id}-${k+1}`,companyId,opportunityId:opp.id,date:d,fromPersonId:opp.stakeholderIds[k],toPersonId:opp.stakeholderIds[k+1],channel:pick(["internal_email","meeting_note","internal_chat"]),topic:k===0?"Требования ИБ":"Бюджет закупки",summary:opp.stage==="lost"?"Обсуждается отказ от текущего предложения.":"Уточняются условия и участники согласования.",synthetic:true});
   referrals.push({id:`referral-${opp.id}-${k+1}`,companyId,opportunityId:opp.id,date:d,fromPersonId:opp.stakeholderIds[k],toPersonId:opp.stakeholderIds[k+1],manager:opp.manager,reason:"Рекомендация подключить коллегу к согласованию",synthetic:true});
  }
  if(opp.stage!=="won"||i%3===0)competitorMentions.push({id:`competitor-${opp.id}`,companyId,opportunityId:opp.id,personId:opp.primaryPersonId,date:date(opp.createdDate,Math.floor(span/2)),competitorAlias:`Условный поставщик ${i%4+1}`,context:opp.stage==="lost"?"Предпочтение альтернативному предложению":"Сравнение поставщиков",synthetic:true});
  decisionOutcomes.push({id:`outcome-${opp.id}`,companyId,opportunityId:opp.id,outcome:opp.stage==="won"?"won":opp.stage==="lost"?"lost":"pending",date:opp.closedDate||null,reason:opp.stage==="won"?"Договор подписан":opp.stage==="lost"?"Согласование отклонено":"Решение пока не принято",evidenceIds:stepIds,synthetic:true});
 }
 const organizationChanges=[],relationshipEvents=[],marketingTouches=[],crmTasks=[];
 for(let i=0;i<8;i++){
  const p=people[(i*4)%people.length],d=date("2025-05-01",i*65+int(0,10));
  organizationChanges.push({id:`org-change-${i+1}`,companyId,personId:p.id,date:d,changeType:i%2?"temporary_project_assignment":"expanded_responsibility",previousTitle:p.title,newTitle:`${p.title} (участник облачного комитета)`,requiresCRMConfirmation:true,synthetic:true});
 }
 for(const p of people){
  const past=[...v1.calls,...v1.emails,...v1.meetings].filter(e=>e.personId===p.id).sort((a,b)=>a.date.localeCompare(b.date));
  for(let k=0;k<4;k++){
   const d=date("2025-06-01",k*145+int(0,15)),evidenceIds=past.filter(x=>x.date<=d).slice(-3).map(x=>x.id);
   relationshipEvents.push({id:`relationship-${p.id}-${k+1}`,companyId,personId:p.id,manager:p.owner,date:d,source:"manual_observation",observedStance:pick(["champion","supporter","neutral","skeptic"]),warmthEstimate:Math.max(1,Math.min(5,p.warmth+int(-2,1))),influenceEstimate:Math.max(1,Math.min(5,p.influence+int(-1,1))),confidence:pick([0.5,0.65,0.8]),evidenceIds,synthetic:true});
  }
  if(p.consentMarketing)for(let k=0;k<2;k++)marketingTouches.push({id:`marketing-${p.id}-${k+1}`,companyId,personId:p.id,date:date("2025-07-01",k*270+int(0,50)),campaign:pick(["Облачная платформа","ИТ-безопасность","Технологический вебинар"]),channel:pick(["webinar","event_invitation","newsletter"]),response:pick(["opened","registered","ignored","clicked"]),consentChecked:true,synthetic:true});
  const dueDate=date("2026-03-01",int(0,230)),status=pick(["completed","completed","overdue"]);
  crmTasks.push({id:`task-${p.id}`,companyId,personId:p.id,opportunityId:null,manager:p.owner,createdDate:date(dueDate,-21),dueDate,status,completedDate:status==="completed"?date(dueDate,-3):null,taskType:"follow_up",synthetic:true});
 }
 for(const opp of opportunities){
  const dueDate=date(opp.createdDate,50),status=opp.stage==="won"?"completed":opp.stage==="lost"?"cancelled":"overdue";
  crmTasks.push({id:`task-${opp.id}`,companyId,personId:opp.primaryPersonId,opportunityId:opp.id,manager:opp.manager,createdDate:date(dueDate,-14),dueDate,status,completedDate:status==="completed"?dueDate:null,taskType:"approval_follow_up",synthetic:true});
 }
 const projects=[{id:"project-bank-cloud",companyId,name:"Миграция облачной платформы",ownerPersonId:it[0].id,startDate:"2025-04-01",synthetic:true},{id:"project-bank-security",companyId,name:"Контур безопасности",ownerPersonId:sec[0].id,startDate:"2025-06-01",synthetic:true},{id:"project-bank-data",companyId,name:"Интеграция данных",ownerPersonId:business[0].id,startDate:"2025-08-01",synthetic:true}];
 const projectMilestones=[],serviceIncidents=[];
 for(const project of projects){
  for(let k=0;k<6;k++){
   const plannedDate=date(project.startDate,50+k*78),delay=k%3===1?int(10,32):0,actualDate=date(plannedDate,delay);
   projectMilestones.push({id:`milestone-${project.id}-${k+1}`,companyId,projectId:project.id,personId:project.ownerPersonId,plannedDate,actualDate:actualDate<=asOf?actualDate:null,status:actualDate>asOf?"planned":delay?"delayed":"completed",delayDays:actualDate<=asOf?delay:null,synthetic:true});
  }
  for(let k=0;k<4;k++){
   const openedDate=date(project.startDate,75+k*105),closedDate=date(openedDate,int(4,30));
   serviceIncidents.push({id:`incident-${project.id}-${k+1}`,companyId,projectId:project.id,personId:project.ownerPersonId,openedDate,closedDate:closedDate<=asOf?closedDate:null,severity:pick(["low","medium","high"]),category:pick(["availability","integration","access","performance"]),synthetic:true});
  }
 }
 const contractLifecycleEvents=[];
 for(const c of v1.contracts){
  for(const a of v1.amendments.filter(x=>x.contractId===c.id))contractLifecycleEvents.push({id:`lifecycle-${a.id}`,companyId,contractId:c.id,personId:a.approvedByPersonId,date:a.date,eventType:"amendment",sourceId:a.id,synthetic:true});
  const d=date(c.signedDate,300);if(d<=asOf)contractLifecycleEvents.push({id:`lifecycle-review-${c.id}`,companyId,contractId:c.id,personId:c.signerPersonId,date:d,eventType:"renewal_review",sourceId:null,synthetic:true});
 }
 const paymentDisputes=[];
 for(const r of v1.receivables.filter(x=>x.status==="overdue"&&x.outstandingRub>0).slice(0,12)){
  const inv=v1.invoices.find(x=>x.id===r.invoiceId),c=v1.contracts.find(x=>x.id===r.contractId);
  paymentDisputes.push({id:`dispute-${r.invoiceId}`,companyId,invoiceId:r.invoiceId,contractId:r.contractId,personId:c.financePersonId,openedDate:date(inv.dueDate,5),closedDate:null,status:"open",disputedAmountRub:Math.min(r.outstandingRub,Math.round(inv.amountRub*0.4/100)*100),reason:"Требуется согласование счёта и акта",synthetic:true});
 }
 const eventIndex=[],push=(r,kind,d,personIds,refs={})=>{if(d>asOf)throw Error("Future event "+r.id);eventIndex.push({id:`event-${r.id}`,sourceId:r.id,kind,date:d,companyId,personIds:[...new Set(personIds.filter(Boolean))],...refs,synthetic:true})};
 for(const [key,kind] of [["calls","call"],["emails","email"],["meetings","meeting"],["manualAnnotations","manual_annotation"]])for(const r of v1[key])push(r,kind,r.date,[r.personId]);
 for(const r of opportunities)push(r,"opportunity_created",r.createdDate,[r.primaryPersonId],{opportunityId:r.id});
 for(const r of approvalSteps)push(r,"approval",r.date,[r.personId],{opportunityId:r.opportunityId});
 for(const r of decisionMeetings)push(r,"decision_meeting",r.date,r.clientAttendeeIds,{opportunityId:r.opportunityId});
 for(const r of clientInternalMessages)push(r,"client_internal",r.date,[r.fromPersonId,r.toPersonId],{opportunityId:r.opportunityId});
 for(const r of referrals)push(r,"referral",r.date,[r.fromPersonId,r.toPersonId],{opportunityId:r.opportunityId});
 for(const r of competitorMentions)push(r,"competitor_mention",r.date,[r.personId],{opportunityId:r.opportunityId});
 for(const r of organizationChanges)push(r,"org_change",r.date,[r.personId]);
 for(const r of relationshipEvents)push(r,"relationship_observation",r.date,[r.personId]);
 for(const r of marketingTouches)push(r,"marketing_touch",r.date,[r.personId]);
 for(const r of crmTasks)push(r,"task_created",r.createdDate,[r.personId],{opportunityId:r.opportunityId});
 for(const r of projectMilestones)if(r.actualDate)push(r,"milestone",r.actualDate,[r.personId],{projectId:r.projectId});
 for(const r of serviceIncidents)push(r,"incident",r.openedDate,[r.personId],{projectId:r.projectId});
 for(const r of v1.contracts)push(r,"contract_signed",r.signedDate,[r.signerPersonId,r.procurementPersonId,r.financePersonId],{contractId:r.id,opportunityId:r.opportunityId});
 for(const r of contractLifecycleEvents)push(r,"contract_lifecycle",r.date,[r.personId],{contractId:r.contractId});
 for(const r of v1.invoices)push(r,"invoice",r.issuedDate,[r.financePersonId],{contractId:r.contractId});
 for(const r of v1.payments)push(r,"payment",r.date,[],{contractId:r.contractId});
 for(const r of paymentDisputes)push(r,"payment_dispute",r.openedDate,[r.personId],{contractId:r.contractId});
 eventIndex.sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id));
 const degrees=new Map(people.map(p=>[p.id,0]));
 for(const r of crm.relations.filter(x=>x.companyId===companyId)){degrees.set(r.from,(degrees.get(r.from)||0)+1);degrees.set(r.to,(degrees.get(r.to)||0)+1)}
 const personSnapshots=[];
 for(const p of people)for(const cutoff of ["2025-10-01","2026-01-01","2026-04-01","2026-07-01"]){
  const start=date(cutoff,-90),future=date(cutoff,90);
  const count=kind=>eventIndex.filter(e=>e.kind===kind&&e.personIds.includes(p.id)&&e.date>start&&e.date<=cutoff).length;
  const prev=eventIndex.filter(e=>["call","email","meeting","decision_meeting"].includes(e.kind)&&e.personIds.includes(p.id)&&e.date<=cutoff);
  const contracts=v1.contracts.filter(c=>[c.signerPersonId,c.procurementPersonId,c.financePersonId].includes(p.id)&&c.signedDate<=cutoff);
  const overdueExposureRub=v1.invoices.filter(i=>contracts.some(c=>c.id===i.contractId)&&i.issuedDate<=cutoff&&i.dueDate<cutoff).reduce((sum,i)=>sum+Math.max(0,i.amountRub-v1.payments.filter(q=>q.invoiceId===i.id&&q.date<=cutoff).reduce((s,q)=>s+q.amountRub,0)),0);
  const nextMeetings=eventIndex.filter(e=>["meeting","decision_meeting"].includes(e.kind)&&e.personIds.includes(p.id)&&e.date>cutoff&&e.date<=future).length;
  personSnapshots.push({id:`snapshot-${p.id}-${cutoff}`,companyId,personId:p.id,asOf:cutoff,featureWindowDays:90,features:{calls90d:count("call"),emails90d:count("email"),meetings90d:count("meeting")+count("decision_meeting"),approvals90d:count("approval"),daysSinceLastContact:prev.length?days(prev[prev.length-1].date,cutoff):null,graphDegree:degrees.get(p.id)||0,overdueExposureRub},labels:{meetingNext90d:nextMeetings>0?1:0},labelWindowEnd:future,synthetic:true});
 }
 const opportunitySnapshots=[];
 for(const opp of opportunities){
  const outcome=decisionOutcomes.find(x=>x.opportunityId===opp.id);
  for(const offset of [21,45]){
   const cutoff=date(opp.createdDate,offset);if(cutoff>=asOf||(opp.closedDate&&cutoff>=opp.closedDate))continue;
   const end=date(cutoff,180),label=outcome.date&&outcome.date<=end?(outcome.outcome==="won"?1:0):null;
   opportunitySnapshots.push({id:`snapshot-${opp.id}-${offset}`,companyId,opportunityId:opp.id,asOf:cutoff,features:{daysOpen:offset,approvedCount:approvalSteps.filter(x=>x.opportunityId===opp.id&&x.status==="approved"&&x.date<=cutoff).length,rejectedCount:approvalSteps.filter(x=>x.opportunityId===opp.id&&x.status==="rejected"&&x.date<=cutoff).length,competitorMentions:competitorMentions.filter(x=>x.opportunityId===opp.id&&x.date<=cutoff).length,decisionMeetings:decisionMeetings.filter(x=>x.opportunityId===opp.id&&x.date<=cutoff).length,estimatedAmountRub:opp.estimatedAmountRub},labels:{wonWithin180d:label},labelWindowEnd:end,synthetic:true});
  }
 }
 const result={...v1,metadata:{...v1.metadata,dataset:"lpr_bank_synthetic_v2",version:2,seed,asOf,warning:"ALL DATA FICTIONAL. NOT REAL CLIENT ACTIVITY, FINANCE OR VALIDATED ML LABELS."},opportunities,approvalSteps,decisionMeetings,clientInternalMessages,referrals,competitorMentions,decisionOutcomes,organizationChanges,relationshipEvents,marketingTouches,crmTasks,projects,projectMilestones,serviceIncidents,contractLifecycleEvents,paymentDisputes,eventIndex,personSnapshots,opportunitySnapshots};
 const errors=[],allIds=new Set();
 for(const [key,arr] of Object.entries(result))if(Array.isArray(arr))for(const r of arr){
  if(!r||typeof r!=="object"||!r.id)continue;
  if(allIds.has(r.id))errors.push("Duplicate "+r.id);allIds.add(r.id);
  for(const field of ["personId","primaryPersonId","fromPersonId","toPersonId","signerPersonId","financePersonId","procurementPersonId","ownerPersonId"])if(r[field]&&!idSet.has(r[field]))errors.push("Unknown "+r.id+" "+field);
 }
 for(const r of marketingTouches)if(!byId.get(r.personId).consentMarketing)errors.push("Consent "+r.id);
 for(const r of eventIndex)for(const p of r.personIds)if(!idSet.has(p))errors.push("Event person "+r.id);
 for(const r of personSnapshots)if(r.labelWindowEnd>asOf)errors.push("Future target "+r.id);
 for(const r of opportunitySnapshots)if(r.labels.wonWithin180d!==null){const o=decisionOutcomes.find(x=>x.opportunityId===r.opportunityId);if(!o.date||o.date>r.labelWindowEnd)errors.push("Leaked label "+r.id)}
 if(errors.length)throw Error(errors.slice(0,12).join("; "));
 return result;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
 const crm=JSON.parse(readFileSync(resolve(root,'src/data/crm.json'),'utf8'));
 const v1=JSON.parse(readFileSync(resolve(root,'src/data/synthetic/bank_ml_v1.json'),'utf8'));
 const out=resolve(root,'src/data/synthetic/bank_ml_v2.json');
 mkdirSync(dirname(out),{recursive:true});
 writeFileSync(out,JSON.stringify(generateV2(crm,v1),null,2)+'\n','utf8');
 console.log('Generated',out);
}
