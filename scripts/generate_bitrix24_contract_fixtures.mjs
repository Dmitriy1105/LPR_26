// Contract-oriented Bitrix24 legacy REST fixtures, no network access.
// Regenerate: node scripts/generate_bitrix24_contract_fixtures.mjs
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
export function generateFixtures(crm,bank){
 const company=crm.companies.find(c=>c.id==="bank"),people=crm.people.filter(p=>p.companyId==="bank");
 if(!company||people.length!==30||bank.metadata.companyId!=="bank")throw Error("Dataset mismatch");
 const managers=[...new Set(people.map(p=>p.owner))].sort(),users=Object.fromEntries(managers.map((m,i)=>[m,17+i]));
 const contactIds=Object.fromEntries(people.map((p,i)=>[p.id,1001+i])),dealIds=Object.fromEntries(bank.opportunities.map((o,i)=>[o.id,2001+i]));
 const invoiceIds=Object.fromEntries(bank.invoices.map((x,i)=>[x.id,4001+i])),activityIds={},taskIds=Object.fromEntries(bank.crmTasks.map((x,i)=>[x.id,9001+i]));
 const iso=(d,t="12:00:00")=>d?`${d}T${t}+03:00`:null;
 const plus=(d,t,m)=>{const parts=t.split(":").map(Number);const z=new Date(Date.UTC(...d.split("-").map((v,i)=>Number(v)-(i===1?1:0)),parts[0],parts[1],parts[2]||0));if(!Number.isFinite(z.getTime()))throw Error(`Bad time ${d} ${t}`);z.setUTCMinutes(z.getUTCMinutes()+m);return z.toISOString().slice(0,19)+"+03:00"};
 const companies=[{id:42,title:company.name,comments:company.description,assignedById:users[people[0].owner]}];
 const contacts=people.map(p=>{const parts=p.name.trim().split(/\s+/);return {id:contactIds[p.id],name:parts[0],lastName:parts.length>1?parts[1]:"",secondName:parts.length>2?parts.slice(2).join(" "):undefined,post:p.title,companyId:42,assignedById:users[p.owner],typeId:"CLIENT"};});
 const deals=bank.opportunities.map(o=>({id:dealIds[o.id],title:`${company.initiative} — ${o.id}`,companyId:42,contactIds:o.stakeholderIds.map(x=>contactIds[x]).filter(Boolean),assignedById:users[o.manager],stageId:o.stage==="won"?"WON":o.stage==="lost"?"LOSE":"NEW",closed:["won","lost"].includes(o.stage),opportunity:o.estimatedAmountRub,currencyId:"RUB",begindate:o.createdDate,closedate:o.closedDate||null}));
 const invoices=bank.invoices.map(x=>({id:invoiceIds[x.id],title:`Счёт ${x.id}`,accountNumber:x.id,companyId:42,opportunity:x.amountRub,currencyId:x.currency||"RUB",createdTime:iso(x.issuedDate)}));
 const activities=[...bank.calls.map(x=>({x,kind:"call"})),...bank.emails.map(x=>({x,kind:"email"})),...bank.meetings.map(x=>({x,kind:"meeting"}))].sort((a,b)=>a.x.date.localeCompare(b.x.date)||a.x.id.localeCompare(b.x.id)).map(({x,kind},i)=>{
  activityIds[x.id]=5001+i;const t=kind==="call"?x.startTime.padStart(5,"0")+":00":"12:00:00",minutes=kind==="call"?x.durationMinutes:kind==="meeting"?x.durationMinutes:5;
  const owner=contactIds[x.personId];if(!owner)throw Error(`Unknown contact ${x.id}`);
  return {ID:String(5001+i),OWNER_ID:String(owner),OWNER_TYPE_ID:"3",TYPE_ID:kind==="call"?"2":kind==="email"?"4":"1",SUBJECT:kind==="call"?`Звонок: ${x.topic}`:kind==="email"?x.subject:`Встреча: ${x.topic}`,DESCRIPTION:kind==="call"?`Тема звонка: ${x.topic}`:kind==="email"?x.body:x.minutes,DESCRIPTION_TYPE:"1",START_TIME:iso(x.date,t),END_TIME:plus(x.date,t,minutes),RESPONSIBLE_ID:String(users[x.manager]),COMPLETED:"Y",...(kind!=="meeting"?{DIRECTION:kind==="email"&&x.direction==="incoming"?"1":"2"}:{}),COMMUNICATIONS:[{ENTITY_ID:String(owner),ENTITY_TYPE_ID:"3",...(kind==="email"?{TYPE:"EMAIL",VALUE:x.direction==="incoming"?x.from:x.to}:kind==="call"?{TYPE:"PHONE"}:{})}]};
 });
 const tasks=bank.crmTasks.filter(t=>t.status!=="cancelled").map(t=>({id:String(taskIds[t.id]),title:t.taskType==="follow_up"?"Связаться с клиентом":"Согласовать дальнейшие действия",description:`Задача по клиенту ${company.name}`,createdDate:iso(t.createdDate),deadline:iso(t.dueDate),closedDate:iso(t.completedDate),responsibleId:String(users[t.manager]),status:t.status==="completed"?"5":"2",ufCrmTask:[`C_${contactIds[t.personId]}`,...(t.opportunityId?[`D_${dealIds[t.opportunityId]}`]:[])]}));
 const defs=[["companies","crm.item.list",4,"result.items",companies],["contacts","crm.item.list",3,"result.items",contacts],["deals","crm.item.list",2,"result.items",deals],["invoices","crm.item.list",31,"result.items",invoices],["activities","crm.activity.list",null,"result",activities],["tasks","tasks.task.list",null,"result.tasks",tasks]];
 const pages={},methods=[];
 for(const [key,method,entityTypeId,resultPath,rows] of defs){
  const pageInfo=[];for(let i=0;i<rows.length;i+=50){const file=`${key}/page_${String(i/50+1).padStart(3,"0")}.json`,items=rows.slice(i,i+50);pages[file]={result:resultPath==="result.items"?{items}:resultPath==="result.tasks"?{tasks:items}:items,total:rows.length,...(i+50<rows.length?{next:i+50}:{})};pageInfo.push({start:i,file,count:items.length})}
  methods.push({key,method,...(entityTypeId?{entityTypeId}:{}),resultPath,recordCount:rows.length,pages:pageInfo,requestExample:method==="tasks.task.list"?{method,params:{order:{ID:"asc"},filter:{},select:["ID","TITLE","DESCRIPTION","STATUS","CREATED_DATE","DEADLINE","CLOSED_DATE","RESPONSIBLE_ID","UF_CRM_TASK"],start:0}}:{method,params:{...(entityTypeId?{entityTypeId}:{}),...(method==="crm.item.list"?{select:["*"],order:{id:"ASC"}}:{select:["*","COMMUNICATIONS"],order:{ID:"ASC"}}),start:0}}});
 }
 const errors={access_denied:{error:"ACCESS_DENIED",error_description:"Access denied"},insufficient_scope:{error:"insufficient_scope",error_description:"The request requires higher privileges than provided by the access token"},invalid_credentials:{error:"INVALID_CREDENTIALS",error_description:"Invalid request credentials"}};
 const manifest={synthetic:true,profile:"legacy-rest-v1",apiBase:"/rest/",snapshotDate:bank.metadata.asOf,docsChecked:"2026-11-21",pageSize:50,timezone:"+03:00",sources:["src/data/crm.json","src/data/synthetic/bank_ml_v2.json"],recordCounts:Object.fromEntries(defs.map(x=>[x[0],x[4].length])),methods,errors:Object.keys(errors),excluded:["manualAnnotations","relationshipEvents","personSnapshots","opportunitySnapshots","payments","receivables","contracts","clientInternalMessages","decisionOutcomes"],limitations:["Subset of fields, not real portal data","Saved response pages, not a live REST server","No authorization or access filtering","Email and meeting descriptions illustrative; transcripts not exported","This is legacy REST v1, not REST 3.0"]};
 return {manifest,mapping:{synthetic:true,companyIds:{bank:42},contactIds,dealIds,invoiceIds,activityIds,taskIds,users},pages,errors};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
 const crm=JSON.parse(readFileSync(resolve(root,'src/data/crm.json'),'utf8'));
 const bank=JSON.parse(readFileSync(resolve(root,'src/data/synthetic/bank_ml_v2.json'),'utf8'));
 const out=resolve(root,'src/data/bitrix24_contract_v1');
 const {manifest,mapping,pages,errors}=generateFixtures(crm,bank);
 for(const [name,value] of [['manifest.json',manifest],['id_mapping.json',mapping],...Object.entries(pages),...Object.entries(errors).map(([name,obj])=>['errors/'+name+'.json',obj])]){
  const path=resolve(out,name);mkdirSync(dirname(path),{recursive:true});writeFileSync(path,JSON.stringify(value,null,2)+'\n','utf8');
 }
 console.log('Generated contract fixtures',manifest.recordCounts);
}
