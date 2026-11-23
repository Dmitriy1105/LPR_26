// Generator v3.3.0 — deterministic, CRM-contract-preserving text upgrade.
// Run: node scripts/generate_bitrix24_contract_v3_3_0.mjs
import fs from 'node:fs';
import path from 'node:path';
const root='src/data/bitrix24_contract_v3_2_3';
const actions=["запросил уточнение бюджета","предложил согласовать сроки","отметил необходимость экспертной оценки","попросил подтвердить критерии приёмки","указал на риск задержки","инициировал проверку требований","предложил обсудить альтернативу","попросил подготовить документы"];
const openings=["В рамках темы","При обсуждении вопроса","По направлению","Для согласования темы","В рабочей переписке по вопросу","В ходе уточнения темы"];
const details=["Позиция остаётся предварительной до проверки фактов","Следующий этап зависит от заключения профильных специалистов","Открытые вопросы требуют документального подтверждения","Условия должны быть сопоставлены с бюджетом и сроками","Решение необходимо сверить с требованиями заинтересованных подразделений","Обсуждение не заменяет формального согласования"];
const endings=["Ответственных и сроки требуется зафиксировать в CRM","После получения подтверждения следует согласовать следующий шаг","Недостающие сведения необходимо запросить до принятия решения","Итоги проверки следует оформить отдельным документом","При изменении условий необходимо повторно согласовать план","До завершения проверки окончательное решение не принято"];
const annotations=[];let count=0;const texts=new Set();
for(let i=1;i<=13;i++){
 const file=path.join(root,'activities',`page_${String(i).padStart(3,'0')}.json`);
 const data=JSON.parse(fs.readFileSync(file,'utf8'));
 if(!Array.isArray(data.result))throw Error('Unexpected REST shape: '+file);
 for(const row of data.result){
  const old=String(row.DESCRIPTION);const seg=old.split(/(?<=[.!?])\s+/u);
  // Regeneration is idempotent: a second run preserves the already-generated text.
  if(old.includes('(обращение '+row.ID+')')){
   if(seg.length!==4)throw Error('Four-segment contract violated: '+row.ID);
   count++;texts.add(old);continue;
  }
  if(seg.length!==4||!seg[1].includes('функциональные роли:'))throw Error('Unexpected original segments: '+row.ID);
  const id=Number(row.ID),topic=String(row.SUBJECT||'текущие условия').split(':').slice(-1)[0].trim();
  const action=actions[(id*17+3)%actions.length];
  const second=seg[1].replace(/\.$/,'')+'; по обсуждаемому вопросу представитель клиента '+action+'.';
  const description=`${openings[id%openings.length]} «${topic}» (обращение ${id}) уточнили исходные условия. ${second} ${details[(id*7+1)%details.length]}. ${endings[(id*11+2)%endings.length]}.`;
  if(description.split(/(?<=[.!?])\s+/u).length!==4)throw Error('Bad segmentation: '+id);
  row.DESCRIPTION=description;count++;texts.add(description);
 }
 fs.writeFileSync(file,JSON.stringify(data,null,2)+'\n');
}
if(count!==630||texts.size!==630)throw Error('Count or uniqueness check failed: '+count+'/'+texts.size);
console.log(JSON.stringify({version:'3.3.0',activities:count,unique_descriptions:texts.size,compatibility:'unchanged CRM schema and page paths',note:'Role cooccurrence does not verify actor identity'},null,2));
