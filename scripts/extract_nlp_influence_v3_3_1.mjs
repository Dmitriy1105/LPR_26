// Independent text-only extraction: does not read ground_truth.json.
import fs from 'node:fs';
const root='src/data/bitrix24_contract_v3_2_3';
const contacts=JSON.parse(fs.readFileSync(root+'/contacts/page_001.json','utf8')).result.items;
const names=contacts.map(c=>({id:c.id,name:c.name+' '+c.lastName}));
const scenarios=JSON.parse(fs.readFileSync('src/data/nlp_enrichment_v3_3_1/scenarios.json','utf8'));
const verbs=[['рекомендовал','recommendation'],['попросил','request'],['поручил','delegation'],['убедил','support']];
const out=[];
for(const s of scenarios){
 let found=null;
 for(const a of names)for(const b of names){
  if(a.id===b.id)continue;
  const prefix=a.name+' ';
  if(!s.text.startsWith(prefix))continue;
  for(const [verb,type] of verbs){
   if(s.text.startsWith(prefix+verb+' '+b.name+' ')){
    let relation_type=type;
    if(verb==='попросил'&&s.text.includes('пересмотреть бюджет'))relation_type='objection';
    found={activity_id:s.activity_id,document_id:s.document_id,actor_contact_id:a.id,target_contact_id:b.id,relation_type,evidence_text:s.text,status:'synthetic_text_extracted_unverified',influence_verified:false,requires_human_review:true};
   }
  }
 }
 if(found)out.push(found);
}
fs.writeFileSync('src/data/nlp_enrichment_v3_3_1/extracted_relations.json',JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({scenarios:scenarios.length,extracted:out.length,verified_influence:0}));
