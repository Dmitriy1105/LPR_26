// Synthetic NLP corpus, linked to Bitrix24-compatible activity identifiers.
// No transcript or email body here represents an actual customer conversation.
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateFixtures} from './generate_bitrix24_contract_fixtures.mjs';

const normalize = value => String(value ?? '').trim();
const snippets = [
  ['Согласование', 'Для принятия решения потребуется согласование с руководителем подразделения.', 'Просьба направить расчёт стоимости и сроки внедрения.'],
  ['Бюджет', 'Предложение интересно, но необходимо уточнить бюджет и условия оплаты.', 'Финансовый отдел должен подтвердить условия.'],
  ['Техническая оценка', 'Техническая команда проверит совместимость решения с нашей инфраструктурой.', 'После проверки организуем обсуждение с ответственным специалистом.'],
  ['Сроки', 'Для нас важны сроки запуска и доступность команды внедрения.', 'Подготовьте план работ с ключевыми этапами.'],
  ['Риски', 'Перед согласованием нужно оценить риски и условия сопровождения.', 'Предлагаю обсудить это с коллегами на следующей встрече.'],
  ['Решение', 'Окончательное решение будет принято после обсуждения с несколькими участниками.', 'Пришлите материалы для внутреннего рассмотрения.']
];
const scenario = i => snippets[i % snippets.length];
const text = value => normalize(value).replace(/\s+/g, ' ');
export function generateNlpCorpus(crm, bank) {
  const {mapping} = generateFixtures(crm, bank);
  const people = new Map(crm.people.map(p => [p.id, p]));
  const documents = [];
  const append = (event, kind, i) => {
    const person = people.get(event.personId);
    if (!person) throw new Error('Unknown communication person: ' + event.personId);
    const activityId = mapping.activityIds[event.id];
    if (!activityId) throw new Error('Unmapped activity: ' + event.id);
    const [subject, customer, next] = scenario(i);
    const topic = text(event.topic || event.subject || subject);
    const manager = text(event.manager || person.owner || 'Менеджер');
    const customerName = text(person.name);
    const utterances = [
      {speaker:'manager',speakerName:manager,startMs:0,endMs:12000,text:'Здравствуйте. Хотел обсудить вопрос: ' + topic + '.'},
      {speaker:'customer',speakerName:customerName,startMs:12000,endMs:27000,text:customer},
      {speaker:'manager',speakerName:manager,startMs:27000,endMs:41000,text:'Понял. Подготовим материалы и уточним необходимые условия.'},
      {speaker:'customer',speakerName:customerName,startMs:41000,endMs:54000,text:next}
    ];
    const base = {id:'nlp_'+event.id,sourceEventId:event.id,crmActivityId:String(activityId),
      contactId:String(mapping.contactIds[event.personId]),date:event.date,kind,
      synthetic:true,language:'ru',provenance:'generated_nlp_scenario_v1'};
    if (kind === 'call') {
      documents.push({...base,documentType:'call_transcript',subject:topic,
        utterances,fullText:utterances.map(u=>u.speakerName+': '+u.text).join('\n'),
        transcriptionStatus:'synthetic_ready'});
    } else if (kind === 'meeting') {
      documents.push({...base,documentType:'meeting_minutes',subject:topic,
        participants:[manager,customerName],utterances,
        fullText:utterances.map(u=>u.speakerName+': '+u.text).join('\n'),
        meetingNotes:text(event.minutes || next)});
    } else {
      const from=text(event.from || manager),to=text(event.to || customerName);
      const body=text(event.body || '');
      const fullBody=body.length>=80?body:
        'Здравствуйте! По теме «'+topic+'» сообщаем следующее. '+customer+' '+next+
        (body?' Дополнительная информация: '+body:'')+' С уважением, участники переписки.';
      documents.push({...base,documentType:'email',subject:text(event.subject || topic),
        from,to,direction:event.direction || 'outgoing',body:fullBody,fullText:fullBody,
        threadId:'thread_'+event.personId,bodyOrigin:body.length>=80?'source_synthetic':'expanded_synthetic'});
    }
  };
  bank.calls.forEach((x,i)=>append(x,'call',i));
  bank.emails.forEach((x,i)=>append(x,'email',i));
  bank.meetings.forEach((x,i)=>append(x,'meeting',i));
  const transcriptResponses = Object.fromEntries(documents.filter(d=>d.kind==='call').map(d=>[
    d.crmActivityId,{result:{transcription:d.fullText}}
  ]));
  const emailResponses = Object.fromEntries(documents.filter(d=>d.kind==='email').map(d=>[
    d.crmActivityId,{result:{activityId:d.crmActivityId,subject:d.subject,from:d.from,to:d.to,
      body:d.body,threadId:d.threadId}}
  ]));
  return {transcriptResponses,emailResponses,metadata:{synthetic:true,version:'nlp-corpus-v1',source:'bank_ml_v2',
    linkedRestProfile:'legacy-rest-v1',note:'Illustrative generated text, not a real call transcript or email export'},
    counts:{calls:bank.calls.length,emails:bank.emails.length,meetings:bank.meetings.length,total:documents.length},
    documents};
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
  const read=p=>JSON.parse(readFileSync(resolve(root,p),'utf8'));
  const corpus=generateNlpCorpus(read('src/data/crm.json'),read('src/data/synthetic/bank_ml_v2.json'));
  const dest=resolve(root,'src/data/synthetic/bank_nlp_corpus_v1.json');
  mkdirSync(dirname(dest),{recursive:true});
  writeFileSync(dest,JSON.stringify({metadata:corpus.metadata,counts:corpus.counts,documents:corpus.documents},null,2)+'\n','utf8');
  const responseDir=resolve(root,'src/data/bitrix24_contract_v1/nlp');
  mkdirSync(responseDir,{recursive:true});
  for(const [name,value] of [
    ['call_transcript_responses.json',{synthetic:true,method:'crm.activity.call.getTranscript',responses:corpus.transcriptResponses}],
    ['email_content_responses.json',{synthetic:true,kind:'synthetic_email_content_adapter',note:'Not a standard Bitrix24 REST method response',responses:corpus.emailResponses}]
  ]) writeFileSync(resolve(responseDir,name),JSON.stringify(value,null,2)+'\n','utf8');
  console.log('Generated NLP corpus:',corpus.counts,'->',dest);
}
