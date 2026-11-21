// Build illustrative Bitrix24 REST-like responses from the normalized synthetic bank dataset.
// Run: node scripts/export_bitrix24_mock.mjs
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
export function exportBitrix24Mock(crm,bank){
 const company=crm.companies.find(c=>c.id==="bank"),people=crm.people.filter(p=>p.companyId==="bank");
 if(!company||people.length!==30||bank.metadata.companyId!=="bank")throw Error("Bank dataset mismatch");
 const companyId=42,companyIds={[company.id]:companyId};
 const userNames=[...new Set(people.map(p=>p.owner))],users=userNames.map((name,i)=>({id:17+i,name:name.split(" ")[0],lastName:name.split(" ").slice(1).join(" "),active:true}));
 const managerId=name=>users.find(u=>`${u.name} ${u.lastName}`===name)?.id||17;
 const contactIds=Object.fromEntries(people.map((p,i)=>[p.id,1001+i]));
 const dealIds=Object.fromEntries(bank.opportunities.map((o,i)=>[o.id,2001+i]));
 const invoiceIds=Object.fromEntries(bank.invoices.map((o,i)=>[o.id,4001+i]));
 const contractIds=Object.fromEntries(bank.contracts.map((o,i)=>[o.id,3001+i]));
 const iso=d=>d?`${d}T12:00:00+03:00`:null;
 const wrap=(items,pageSize=50)=>({result:{items:items.slice(0,pageSize)},total:items.length,...(items.length>pageSize?{next:pageSize}:{})});
 const companies=wrap([{id:companyId,title:company.name,industry:"BANKING",assignedById:users[0].id,comments:company.description}]);
 const contacts=wrap(people.map(p=>({id:contactIds[p.id],name:p.name.split(" ")[0],lastName:p.name.split(" ").slice(1).join(" "),post:p.title,companyId,assignedById:managerId(p.owner),typeId:"CLIENT",sourceId:"OTHER"})));
 const deals=wrap(bank.opportunities.map(o=>({id:dealIds[o.id],title:`${company.name} — ${company.initiative} (${o.id})`,companyId,contactId:contactIds[o.primaryPersonId],assignedById:managerId(o.manager),stageId:o.stage==="won"?"WON":o.stage==="lost"?"LOSE":"NEW",opportunity:o.estimatedAmountRub,currencyId:"RUB",begindate:iso(o.createdDate),closedate:iso(o.closedDate),comments:"Учебная сделка; данные полностью синтетические."})));
 const invoices=wrap(bank.invoices.map(inv=>({id:invoiceIds[inv.id],title:`Счёт ${inv.id}`,companyId,opportunity:inv.amountRub,currencyId:"RUB",createdTime:iso(inv.issuedDate),ufCrmMockDueDate:iso(inv.dueDate)})));
 const activityRows=[];
 for(const x of [...bank.calls,...bank.emails,...bank.meetings]){
  const type=x.channel==="phone"?2:x.channel==="email"?4:1,owner=contactIds[x.personId];
  const description=x.channel==="phone"?x.transcript.map(t=>`${t.speaker}: ${t.text}`).join("\n"):x.channel==="email"?x.body:x.minutes;
  const subject=x.channel==="phone"?`Звонок: ${x.topic}`:x.channel==="email"?x.subject:`Встреча: ${x.topic}`;
  activityRows.push({ID:String(5001+activityRows.length),OWNER_ID:String(owner),OWNER_TYPE_ID:"3",TYPE_ID:String(type),PROVIDER_ID:x.channel==="phone"?"VOXIMPLANT_CALL":x.channel==="email"?"EMAIL":"CRM_MEETING",SUBJECT:subject,DESCRIPTION:description,START_TIME:iso(x.date),END_TIME:iso(x.date),RESPONSIBLE_ID:String(managerId(x.manager)),COMPLETED:"Y",COMMUNICATIONS:[{ENTITY_ID:String(owner),ENTITY_TYPE_ID:"3"}]});
 }
 const activities={result:activityRows.slice(0,50),total:activityRows.length,next:50};
 const taskRows=bank.crmTasks.map((t,i)=>({id:9001+i,title:t.taskType==="follow_up"?"Связаться с клиентом":"Уточнить согласование сделки",description:t.taskType,createdDate:iso(t.createdDate),deadline:iso(t.dueDate),closedDate:iso(t.completedDate),responsibleId:managerId(t.manager),status:t.status==="completed"?"5":t.status==="cancelled"?"7":"2",ufMockContactId:contactIds[t.personId],ufMockDealId:t.opportunityId?dealIds[t.opportunityId]:null}));
 const tasks={result:{tasks:taskRows.slice(0,50)},total:taskRows.length};
 const manifest={synthetic:true,source:"src/data/synthetic/bank_ml_v2.json",snapshotDate:bank.metadata.asOf,apiStyle:"Bitrix24 CRM universal crm.item.list for core entities; legacy crm.activity.list and tasks.task.list for activity/tasks",methods:{"crm.item.list:4":{file:"crm_company_list.json",entityTypeId:4},"crm.item.list:3":{file:"crm_contact_list.json",entityTypeId:3},"crm.item.list:2":{file:"crm_deal_list.json",entityTypeId:2},"crm.item.list:31":{file:"crm_invoice_list.json",entityTypeId:31},"crm.activity.list":{file:"crm_activity_list.json"},"tasks.task.list":{file:"tasks_task_list.json"}},limitations:["Not captured from a real portal","Representative field subset only","Custom ufCrmMockDueDate and ufMock* are illustrative, not standard Bitrix24 fields","Financial payments, contracts, internal client communications, graph influence and ML labels are not claimed to be native CRM entities","Activity and task fixtures use legacy response conventions and must be checked against target portal and REST version","Pagination fixtures contain only first page; generator stores all records in normalized data"],recordCounts:{companies:1,contacts:people.length,deals:bank.opportunities.length,invoices:bank.invoices.length,activities:activityRows.length,tasks:taskRows.length}};
 const mapping={companyIds,contactIds,dealIds,invoiceIds,contractIds,users:users.map(u=>({id:u.id,name:`${u.name} ${u.lastName}`})),synthetic:true};
 return {manifest,mapping,companies,contacts,deals,invoices,activities,tasks};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
 const crm=JSON.parse(readFileSync(resolve(root,'src/data/crm.json'),'utf8'));
 const bank=JSON.parse(readFileSync(resolve(root,'src/data/synthetic/bank_ml_v2.json'),'utf8'));
 const mock=exportBitrix24Mock(crm,bank),dir=resolve(root,'src/data/bitrix24_mock');
 mkdirSync(dir,{recursive:true});
 for(const [key,filename] of Object.entries({manifest:'manifest.json',mapping:'id_mapping.json',companies:'crm_company_list.json',contacts:'crm_contact_list.json',deals:'crm_deal_list.json',invoices:'crm_invoice_list.json',activities:'crm_activity_list.json',tasks:'tasks_task_list.json'}))writeFileSync(resolve(dir,filename),JSON.stringify(mock[key],null,2)+'\n','utf8');
 console.log('Generated Bitrix24-like mock in',dir);
}
