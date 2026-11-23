// Generator v3.3.1 — additive, deterministic NLP evidence overlay. No CRM mutation.
import fs from 'node:fs';
const root='src/data/bitrix24_contract_v3_2_3';
const contacts=JSON.parse(fs.readFileSync(root+'/contacts/page_001.json','utf8')).result.items;
const names=new Map(contacts.map(c=>[String(c.id),c.name+' '+c.lastName]));
const rows=[];
for(let i=1;i<=13;i++)rows.push(...JSON.parse(fs.readFileSync(root+'/activities/page_'+String(i).padStart(3,'0')+'.json','utf8')).result);
const verbs=[
 {kind:'recommendation',verb:'рекомендовал',ending:'рассмотреть предложение'},
 {kind:'objection',verb:'попросил',ending:'пересмотреть бюджет'},
 {kind:'delegation',verb:'поручил',ending:'подготовить заключение'},
 {kind:'support',verb:'убедил',ending:'поддержать инициативу'},
 {kind:'request',verb:'попросил',ending:'уточнить сроки'}
];
const examples=[],gold=[];
for(const a of rows){
 const ids=[...new Set((a.COMMUNICATIONS||[]).map(x=>String(x.ENTITY_ID)))].filter(x=>names.has(x));
 if(ids.length<2)continue;
 const id=String(a.ID),ix=Number(id)%verbs.length,neg=Number(id)%6===0;
 const v=verbs[ix],actor=ids[0],target=ids[1];
 const evidence=neg
 ? names.get(actor)+' и '+names.get(target)+' участвовали в обсуждении; решение не зафиксировано.'
 : names.get(actor)+' '+v.verb+' '+names.get(target)+' '+v.ending+'.';
 const item={activity_id:id,document_id:'activity:'+id,company_id:42,source:'synthetic_nlp_enrichment_v3.3.1',text:evidence,participant_contact_ids:ids.map(Number),synthetic:true};
 examples.push(item);
 gold.push({activity_id:id,document_id:item.document_id,relation_type:neg?null:v.kind,actor_contact_id:neg?null:Number(actor),target_contact_id:neg?null:Number(target),evidence_text:neg?null:evidence,is_positive:!neg,annotation_source:'generator_v3.3.1',verification_scope:'synthetic_ground_truth_only'});
}
if(rows.length!==630||examples.length!==90)throw Error('CRM baseline drift: '+rows.length+'/'+examples.length);
fs.mkdirSync('src/data/nlp_enrichment_v3_3_1',{recursive:true});
fs.writeFileSync('src/data/nlp_enrichment_v3_3_1/scenarios.json',JSON.stringify(examples,null,2)+'\n');
fs.writeFileSync('src/data/nlp_enrichment_v3_3_1/ground_truth.json',JSON.stringify(gold,null,2)+'\n');
console.log(JSON.stringify({activities:rows.length,scenarios:examples.length,positives:gold.filter(x=>x.is_positive).length,negatives:gold.filter(x=>!x.is_positive).length}));
