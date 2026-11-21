// Normalize Bitrix24 legacy REST JSON into text documents for NLP.
// No dependency on synthetic/nlp_v1 files.
export function extractRestNlpDocuments(activityPages, transcriptResponses) {
  const activities=activityPages.flatMap(page=>{
    if(!Array.isArray(page?.result)) throw new TypeError('crm.activity.list result must be an array');
    return page.result;
  });
  const responses=transcriptResponses?.responses ?? transcriptResponses;
  if(!responses || typeof responses!=='object') throw new TypeError('Missing call transcript responses');
  const docs=[];
  const seen=new Set();
  for(const a of activities){
    const id=String(a.ID??'');
    if(!id || seen.has(id)) throw new Error('Duplicate or missing activity ID: '+id);
    seen.add(id);
    const kind=String(a.TYPE_ID)==='2'?'call':String(a.TYPE_ID)==='4'?'email':String(a.TYPE_ID)==='1'?'meeting':null;
    if(!kind) continue;
    const transcript=kind==='call'?(responses[id]?.result?.transcription??null):null;
    if(transcript!==null && typeof transcript!=='string')throw new TypeError('Invalid transcript for '+id);
    const body=kind==='call'?transcript:a.DESCRIPTION;
    const status=typeof body==='string'&&body.trim()?'ready':'missing_text';
    docs.push({
      source:'bitrix24_rest',activityId:id,contactId:String(a.OWNER_ID??''),
      activityType:kind,date:a.START_TIME??null,subject:a.SUBJECT??'',
      text:status==='ready'?body:null,status,
      textSource:kind==='call'?'crm.activity.call.getTranscript':'crm.activity.list.DESCRIPTION',
      responsibleId:String(a.RESPONSIBLE_ID??'')
    });
  }
  return docs;
}
