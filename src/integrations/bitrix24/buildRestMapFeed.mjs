import {extractRestNlpDocuments} from './extractRestNlpDocuments.mjs';

// Independent REST source for a decision-map data layer.
// Never infers manual influence, decision role, stance or relationship strength.
export function buildRestMapFeed(contactPage, activityPages, transcriptResponses) {
 const contacts=contactPage?.result?.items;
 if(!Array.isArray(contacts))throw new TypeError('crm.item.list contacts result.items must be an array');
 const people=contacts.map(c=>({
  id:String(c.id),name:[c.lastName,c.name,c.secondName].filter(Boolean).join(' '),
  companyId:String(c.companyId??''),title:c.post??'',
  source:'bitrix24_rest',decisionRole:null,influence:null,stance:null
 }));
 const known=new Set(people.map(p=>p.id));
 if(known.size!==people.length)throw new Error('Duplicate contact ID');
 const documents=extractRestNlpDocuments(activityPages,transcriptResponses);
 const interactions=documents.map(d=>{
  if(!known.has(d.contactId))throw new Error('Unknown REST contact '+d.contactId);
  return {id:d.activityId,personId:d.contactId,date:d.date,channel:d.activityType,
   summary:d.text??'',textStatus:d.status,textSource:d.textSource,source:'bitrix24_rest'};
 });
 return {source:'bitrix24_rest',people,interactions};
}
