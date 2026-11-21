// Reproducible fictional dataset for the existing bank contacts in src/data/crm.json.
// Run from repository root: node scripts/generate_synthetic_bank_data.mjs
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';

export function generate(crm,seed=20261121){
 const people=crm.people.filter(p=>p.companyId==="bank");
 if(people.length!==30)throw Error("Expected 30 bank contacts");
 const managers=[...new Set(people.map(p=>p.owner))];
 let state=seed>>>0;
 const rand=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)/4294967296};
 const int=(a,b)=>a+Math.floor(rand()*(b-a+1));
 const pick=a=>a[int(0,a.length-1)];
 const add=(iso,days)=>{const d=new Date(iso+"T12:00:00Z");d.setUTCDate(d.getUTCDate()+days);return d.toISOString().slice(0,10)};
 const asOf="2026-11-21",before=d=>d<=asOf;
 const money=n=>Math.round(n/100)*100;
 const topics=["сроки миграции","информационная безопасность","бюджет проекта","технические требования","согласование договора","график внедрения","облачная инфраструктура","условия поддержки"];
 const positions={champion:"поддерживает инициативу",supporter:"готов рассмотреть предложение",neutral:"ожидает дополнительных аргументов",skeptic:"выражает сомнения"};
 const tone={champion:"позитивный",supporter:"позитивный",neutral:"нейтральный",skeptic:"сдержанный"};
 const calls=[],emails=[],meetings=[],manualAnnotations=[];
 const byPerson=new Map(people.map(p=>[p.id,[]]));
 const store=(arr,r)=>{arr.push(r);byPerson.get(r.personId).push({id:r.id,date:r.date})};
 for(const p of people){
  const manager=p.owner;
  for(let k=0;k<6;k++){
   const date=add("2025-03-01",k*90+int(0,35)),topic=pick(topics),id=`call-${p.id}-${k+1}`;
   store(calls,{id,companyId:"bank",personId:p.id,manager,date,startTime:`${int(9,17)}:${pick(["00","15","30","45"])}`,durationMinutes:int(6,42),channel:"phone",topic,disposition:pick(["follow_up","clarification","next_meeting","materials_requested"]),sentiment:tone[p.stance],transcript:[
    {speaker:"manager",text:`Добрый день, ${p.name.split(" ")[0]}. Хотел уточнить статус вопроса: ${topic}.`},
    {speaker:"client",text:`Сейчас ${positions[p.stance]}. Важно уточнить сроки и ответственных.`},
    {speaker:"manager",text:"Подготовим материалы и согласуем следующий шаг."},
    {speaker:"client",text:"Направьте краткое резюме и предложите время обсуждения."}
   ],synthetic:true});
  }
  for(let k=0;k<9;k++){
   const date=add("2025-01-15",k*68+int(0,28)),topic=pick(topics),id=`email-${p.id}-${k+1}`,outgoing=k%2===0;
   store(emails,{id,companyId:"bank",personId:p.id,manager,date,channel:"email",direction:outgoing?"outgoing":"incoming",from:outgoing?`manager.${managers.indexOf(manager)+1}@vendor.example`:`${p.id}@client.example`,to:outgoing?`${p.id}@client.example`:`manager.${managers.indexOf(manager)+1}@vendor.example`,subject:`Облачная платформа — ${topic}`,body:outgoing?`Здравствуйте, ${p.name.split(" ")[0]}! Направляем материалы по теме «${topic}». Просим сообщить замечания и удобную дату следующего обсуждения. С уважением, ${manager}.`:`Добрый день! Получили материалы по теме «${topic}». ${positions[p.stance][0].toUpperCase()+positions[p.stance].slice(1)}. Просим уточнить условия, сроки и ответственную сторону. С уважением, ${p.name}.`,sentiment:tone[p.stance],synthetic:true});
  }
  for(let k=0;k<3;k++){
   const date=add("2025-05-10",k*220+int(0,30)),topic=pick(topics),id=`meeting-${p.id}-${k+1}`;
   store(meetings,{id,companyId:"bank",personId:p.id,clientAttendeeIds:[p.id],manager,ourAttendees:[manager],date,channel:pick(["video","office","onsite"]),durationMinutes:pick([30,45,60,90]),topic,minutes:`Обсуждали ${topic}. Представитель клиента ${positions[p.stance]}. Отмечены вопросы по стоимости, рискам внедрения и согласованию графика.`,decisions:["Подготовить уточнённые материалы","Согласовать дальнейшую встречу"],nextActionDue:add(date,14),synthetic:true});
  }
  for(let k=0;k<4;k++){
   const date=add("2025-03-20",k*175+int(0,20)),id=`note-${p.id}-${k+1}`,evidenceIds=byPerson.get(p.id).filter(e=>e.date<=date).slice(-3).map(e=>e.id);
   manualAnnotations.push({id,companyId:"bank",personId:p.id,manager,date,source:"manager_manual",stance:p.stance,warmth:Math.max(1,Math.min(5,p.warmth+int(-1,1))),influence:Math.max(1,Math.min(5,p.influence+int(-1,1))),confidence:pick([0.55,0.65,0.75,0.85]),note:`По оценке менеджера контакт ${positions[p.stance]}; важны ${p.interests.join(" и ").toLowerCase()}. Оценка требует подтверждения.`,evidenceIds,synthetic:true});
  }
 }
 const decision=people.filter(p=>p.decisionRole==="decision_maker"),proc=people.filter(p=>p.department==="Закупки"),fin=people.filter(p=>p.department==="Финансы");
 const opportunities=[],contracts=[],amendments=[],invoices=[],payments=[];
 for(let i=0;i<10;i++){
  const signer=decision[i%decision.length],buyer=proc[i%proc.length],controller=fin[i%fin.length];
  const signedDate=add("2025-03-01",i*44+int(0,18)),createdDate=add(signedDate,-int(70,130)),id=`contract-bank-${String(i+1).padStart(3,"0")}`;
  const amount=money(int(24,145)*100000),manager=signer.owner;
  opportunities.push({id:`opp-bank-${i+1}`,companyId:"bank",primaryPersonId:signer.id,stakeholderIds:[signer.id,buyer.id,controller.id],manager,createdDate,stage:"won",closedDate:signedDate,estimatedAmountRub:amount,synthetic:true});
  contracts.push({id,opportunityId:`opp-bank-${i+1}`,companyId:"bank",signerPersonId:signer.id,procurementPersonId:buyer.id,financePersonId:controller.id,manager,signedDate,effectiveDate:signedDate,endDate:add(signedDate,730),initialAmountRub:amount,currency:"RUB",status:"active",subject:"Внедрение и сопровождение облачной платформы",synthetic:true});
  for(let j=0;j<2;j++){
   const date=add(signedDate,75+j*155);
   if(before(date))amendments.push({id:`amend-bank-${i+1}-${j+1}`,contractId:id,companyId:"bank",date,kind:j===0?"scope_change":"schedule_change",amountDeltaRub:j===0?money(amount*pick([0.03,0.05,0.08])):0,daysDelta:j===1?pick([15,30,45]):0,reason:j===0?"Дополнительный объём услуг":"Корректировка графика этапов",approvedByPersonId:signer.id,synthetic:true});
  }
  for(let j=0;j<5;j++){
   const issuedDate=add(signedDate,30+j*85);
   if(!before(issuedDate))continue;
   const invoiceId=`invoice-bank-${i+1}-${j+1}`,invoiceAmount=money(amount/7);
   const dueDate=add(issuedDate,35);
   invoices.push({id:invoiceId,contractId:id,companyId:"bank",issuedDate,dueDate,amountRub:invoiceAmount,currency:"RUB",financePersonId:controller.id,synthetic:true});
   const mode=int(0,4),fractions=mode===0?[]:mode===1?[0.4]:mode===2?[0.65]:mode===3?[1]:[0.5,0.5];
   let paid=0;
   for(let z=0;z<fractions.length;z++){
    const date=add(issuedDate,12+z*25+int(0,15));
    if(!before(date))continue;
    const value=money(invoiceAmount*fractions[z]);if(value<=0||paid+value>invoiceAmount)continue;
    payments.push({id:`payment-bank-${i+1}-${j+1}-${z+1}`,invoiceId,contractId:id,companyId:"bank",date,amountRub:value,currency:"RUB",method:"bank_transfer",synthetic:true});paid+=value;
   }
  }
 }
 const paymentByInvoice=new Map();
 for(const p of payments)paymentByInvoice.set(p.invoiceId,(paymentByInvoice.get(p.invoiceId)||0)+p.amountRub);
 const receivables=invoices.map(inv=>{const paidRub=paymentByInvoice.get(inv.id)||0;const outstandingRub=inv.amountRub-paidRub;return {invoiceId:inv.id,contractId:inv.contractId,companyId:"bank",asOf,paidRub,outstandingRub,daysOverdue:outstandingRub>0&&inv.dueDate<asOf?Math.floor((new Date(asOf)-new Date(inv.dueDate))/86400000):0,status:outstandingRub===0?"paid":inv.dueDate<asOf?"overdue":"open",synthetic:true}});
 const result={metadata:{dataset:"lpr_bank_synthetic_v1",synthetic:true,companyId:"bank",companyName:crm.companies.find(c=>c.id==="bank").name,source:"src/data/crm.json",seed,asOf,periodStart:"2025-01-01",currency:"RUB",warning:"FICTIONAL DEMO DATA; not real communications, contracts, debt, or model evidence"},managers,contactIds:people.map(p=>p.id),calls,emails,meetings,manualAnnotations,opportunities,contracts,amendments,invoices,payments,receivables};
 return result;
}

if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
 const crm=JSON.parse(readFileSync(resolve(root,'src/data/crm.json'),'utf8'));
 const result=generate(crm);
 const output=resolve(root,'src/data/synthetic/bank_ml_v1.json');
 mkdirSync(dirname(output),{recursive:true});
 writeFileSync(output,JSON.stringify(result,null,2)+'\n','utf8');
 console.log('Wrote',output,'contacts',result.contactIds.length,'calls',result.calls.length,'emails',result.emails.length);
}
