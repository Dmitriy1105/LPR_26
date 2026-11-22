// Scenario-based synthetic communication generator v3.2.
// Keeps the v3.1 normalized schema and REST fixture contract.
// Run: node scripts/generate_synthetic_bank_v3_2.mjs
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { generateV3 } from "./generate_synthetic_bank_v3.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DEFAULT_SEED = 20261122;

function hash32(value) {
  let h = 2166136261;
  for (const ch of String(value)) {
    h ^= ch.charCodeAt(0);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
function pick(list, key) {
  if (!list.length) throw new Error("Cannot pick from an empty list");
  return list[hash32(key) % list.length];
}
function dateRu(value) {
  const [y, m, d] = String(value || "").slice(0, 10).split("-");
  return y && m && d ? [d, m, y].join(".") : "дата не указана";
}
function addDays(value, days) {
  const d = new Date(String(value).slice(0, 10) + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}
function firstName(people, id) {
  return (people.get(id)?.name || "коллега").trim().split(/\s+/)[0];
}
function fullName(people, id) {
  return people.get(id)?.name || "коллега";
}
function profile(topic) {
  const t = String(topic || "").toLowerCase();
  if (/бюджет|закуп|финанс/.test(t)) return {
    subject: "финансовые параметры и порядок согласования расходов",
    evidence: ["расчет полной стоимости владения", "лимиты подразделений и резерв бюджета", "состав затрат на внедрение и сопровождение", "основания для изменения сметы"],
    decision: ["финансовый блок подтвердит доступный лимит", "закупки сверят коммерческие условия", "руководитель направления рассмотрит итоговый вариант"]
  };
  if (/безопас|иб|доступ|угроз/.test(t)) return {
    subject: "требования информационной безопасности и контроль доступа",
    evidence: ["модель угроз и перечень критичных данных", "схема разграничения доступа", "результаты проверки защитных механизмов", "порядок регистрации и разбора инцидентов"],
    decision: ["служба безопасности подготовит заключение", "владелец системы подтвердит модель доступа", "открытые замечания будут вынесены на технический комитет"]
  };
  if (/договор|контракт|юрид/.test(t)) return {
    subject: "договорные условия и распределение обязательств",
    evidence: ["границы ответственности сторон", "порядок приемки и подтверждения результата", "условия изменения объема работ", "сроки согласования приложений"],
    decision: ["юридическая служба сверит редакцию", "закупки соберут консолидированные замечания", "подписание перенесут до закрытия существенных разногласий"]
  };
  if (/миграц|перенос|инфраструкт/.test(t)) return {
    subject: "этапы миграции и готовность инфраструктуры",
    evidence: ["окно переключения и план отката", "зависимости между системами", "критерии готовности среды", "план проверки после переноса"],
    decision: ["ИТ-команда уточнит календарный план", "владелец сервиса подтвердит допустимое окно работ", "переход будет назначен после контрольной проверки"]
  };
  if (/срок|график|этап/.test(t)) return {
    subject: "сроки, зависимости и ответственность за этапы",
    evidence: ["критический путь проекта", "доступность профильных специалистов", "зависимости от внешних поставщиков", "контрольные точки приемки"],
    decision: ["руководители потоков актуализируют даты", "ответственные подтвердят загрузку", "новый график направят участникам на проверку"]
  };
  if (/поддерж|сервис|sla/.test(t)) return {
    subject: "уровень сервиса и порядок обработки обращений",
    evidence: ["время реакции по категориям обращений", "режим работы службы поддержки", "маршрут эскалации", "порядок отчетности по качеству сервиса"],
    decision: ["эксплуатация проверит целевые показатели", "владелец сервиса подтвердит приоритеты", "условия поддержки включат в итоговую спецификацию"]
  };
  if (/техничес|архитект|интеграц/.test(t)) return {
    subject: "архитектура решения и интеграционные ограничения",
    evidence: ["состав интеграционных интерфейсов", "нагрузочные требования", "ограничения текущего ИТ-ландшафта", "критерии технической приемки"],
    decision: ["архитекторы сверят целевую схему", "владельцы систем подтвердят интерфейсы", "спорные вопросы рассмотрят на технической сессии"]
  };
  return {
    subject: "объем работ, риски и порядок принятия решения",
    evidence: ["границы проекта и критерии результата", "необходимые исходные данные", "распределение ответственности", "порядок подтверждения договоренностей"],
    decision: ["ответственные подразделения уточнят позицию", "координатор соберет замечания", "вопрос вернут на совместное рассмотрение"]
  };
}
function stance(sentiment, key) {
  const s = String(sentiment || "").toLowerCase();
  if (/позит|поддерж|champion/.test(s)) return pick([
    "В целом направление поддерживаем, при этом просим отдельно закрепить критерии приемки.",
    "Существенных возражений нет; для перехода дальше необходимо подтвердить ресурсы и сроки.",
    "Предложенный подход можно продолжать прорабатывать после фиксации ответственности.",
    "Готовы поддержать следующий этап, если контрольные условия будут отражены в документах.",
    "По основному направлению позиция положительная, остаются отдельные вопросы реализации."
  ], key);
  if (/негат|скеп|возраж|reject/.test(s)) return pick([
    "В текущем виде предложение вызывает возражения из-за неурегулированных рисков.",
    "Подтвердить вариант сейчас нельзя: часть требований не имеет достаточного обоснования.",
    "Сначала необходимо устранить замечания профильных подразделений.",
    "Предлагаем рассмотреть альтернативу, поскольку текущие условия не закрывают наши ограничения.",
    "Окончательное согласование невозможно до получения подтверждающих расчетов."
  ], key);
  return pick([
    "Окончательную позицию сформируем после проверки исходных данных.",
    "Пока рано подтверждать вариант: необходимо сопоставить несколько условий.",
    "Вопрос остается открытым до получения заключений профильных подразделений.",
    "Для принятия позиции требуется дополнительная информация от владельцев процессов.",
    "Сейчас можем подтвердить только предварительный интерес к дальнейшей проработке."
  ], key);
}
function callDisposition(call, key) {
  const map = {
    materials_requested: "По итогам звонка запросили расчет и исходные материалы.",
    next_meeting: "Стороны договорились назначить отдельную рабочую встречу.",
    clarification: "Зафиксировали вопросы, которые необходимо уточнить до согласования.",
    follow_up: "К обсуждению вернутся после внутренней проверки."
  };
  return map[call.disposition] || pick([
    "Договоренности внесены в перечень дальнейших действий.",
    "Ответственные обменяются материалами до следующего контакта.",
    "Открытые пункты остаются на контроле координаторов."
  ], key);
}

function rewriteCall(call, people, seed) {
  const key = seed + "|" + call.id;
  const name = firstName(people, call.personId);
  const p = profile(call.topic);
  const openers = [
    "Добрый день, " + name + ". Звоню, чтобы сверить статус по теме «" + call.topic + "».",
    name + ", здравствуйте. Предлагаю вернуться к вопросу «" + call.topic + "» и определить следующий шаг.",
    "Связываюсь после прошлого обсуждения: нужно уточнить, как продвинулась проработка темы «" + call.topic + "».",
    "Добрый день. Удобно сейчас обсудить оставшиеся вопросы по направлению «" + call.topic + "»?",
    name + ", добрый день. Хотел согласовать последовательность действий по теме «" + call.topic + "»."
  ];
  const prompts = [
    "В первую очередь важно проверить " + pick(p.evidence, key + "|e1") + ".",
    "Отдельный вопрос — " + pick(p.evidence, key + "|e2") + ".",
    "Для перехода к следующему этапу нужно понять, кто подтвердит " + pick(p.evidence, key + "|e3") + ".",
    "Предлагаю не смешивать технические и организационные вопросы; начнем с пункта «" + pick(p.evidence, key + "|e4") + "»."
  ];
  const clientReplies = [
    stance(call.sentiment, key + "|stance") + " " + pick([
      "Я уточню позицию коллег и вернусь с ответом.",
      "Нужно подключить профильное подразделение, прежде чем подтверждать решение.",
      "Подготовим замечания по каждому открытому пункту.",
      "Сначала сверим документы внутри команды, затем дадим консолидированный ответ.",
      "Могу подтвердить получение информации, но не окончательное решение."
    ], key + "|reply"),
    "По нашей стороне ответственный за этот блок — " + name + ". " + stance(call.sentiment, key + "|stance2"),
    "Сейчас могу обозначить предварительную позицию. " + stance(call.sentiment, key + "|stance3")
  ];
  const next = [
    "Со своей стороны направим краткое резюме и список вопросов.",
    "После звонка закрепим ответственных и контрольные даты.",
    "Я отправлю обновленную версию материалов, чтобы вы могли оставить замечания.",
    "Предлагаю вернуться к обсуждению после получения заключения."
  ];
  call.transcript = [
    { speaker: "manager", text: pick(openers, key + "|open") + " " + pick(prompts, key + "|prompt") },
    { speaker: "client", text: pick(clientReplies, key + "|client") },
    { speaker: "manager", text: callDisposition(call, key + "|disposition") + " " + pick(next, key + "|next") },
    { speaker: "client", text: pick([
      "Хорошо, зафиксируйте договоренности и пришлите материалы.",
      "Пожалуйста, укажите в письме, какие данные нужны от нашей команды.",
      "Согласуем внутри подразделения и сообщим, кто будет владельцем следующего шага.",
      "До получения документов окончательную позицию не подтверждаем.",
      "Давайте сначала закроем технические вопросы, а затем вернемся к срокам."
    ], key + "|close") }
  ];
}

function rewriteEmail(email, people, seed) {
  const key = seed + "|" + email.id;
  const name = firstName(people, email.personId);
  const person = fullName(people, email.personId);
  const subject = email.subject || email.topic || "текущего проекта";
  const p = profile(subject);
  const due = dateRu(addDays(email.date, 2 + hash32(key + "|due") % 8));
  if (email.direction === "incoming") {
    const openings = [
      "Коллеги, добрый день. Направляю позицию по вопросу «" + subject + "».",
      "Добрый день. Возвращаемся к вашему запросу по теме «" + subject + "».",
      "Здравствуйте. Изучили полученные материалы и подготовили комментарии по направлению «" + subject + "».",
      "По итогам внутреннего обсуждения направляем замечания к материалам по теме «" + subject + "».",
      "Подтверждаем получение документов по вопросу «" + subject + "» и сообщаем текущий статус."
    ];
    const evidence = [
      "Просим дополнительно проверить " + pick(p.evidence, key + "|e1") + ".",
      "Для подготовки окончательной позиции не хватает информации о следующем: " + pick(p.evidence, key + "|e2") + ".",
      "В приложенных материалах пока не раскрыт вопрос: " + pick(p.evidence, key + "|e3") + ".",
      "Просим пояснить, каким образом будет подтверждено " + pick(p.evidence, key + "|e4") + "."
    ];
    const endings = [
      "После получения уточнений согласуем дальнейший порядок действий.",
      "До закрытия этих пунктов просим считать позицию предварительной.",
      "Ответственных коллег подключим после того, как получим недостающие сведения.",
      "Просим включить замечания в следующую редакцию документа.",
      "Готовы обсудить вопросы на короткой рабочей сессии."
    ];
    email.body = pick(openings, key + "|open") + " " +
      stance(email.sentiment, key + "|stance") + " " +
      pick(evidence, key + "|evidence") + " " +
      pick(endings, key + "|end") +
      " Дата письма: " + dateRu(email.date) + ". С уважением, " + person + ".";
  } else {
    const openings = [
      "Здравствуйте, " + name + ". Направляем материалы по теме «" + subject + "» для проверки.",
      "Добрый день, " + name + ". По результатам предыдущего обсуждения подготовили обновленную редакцию.",
      "Направляем согласованные на текущем этапе сведения по вопросу «" + subject + "».",
      "В продолжение переписки собрали информацию, необходимую для следующего этапа по теме «" + subject + "».",
      "Подготовили отдельную сводку по открытым вопросам направления «" + subject + "»."
    ];
    const body = [
      "В документе отражены " + pick(p.evidence, key + "|b1") + " и " + pick(p.evidence, key + "|b2") + ".",
      "Отдельно выделили " + pick(p.evidence, key + "|b3") + "; остальные замечания собраны в приложении.",
      "В сводке разделили подтвержденные параметры и вопросы, по которым еще требуется позиция владельца.",
      "Чтобы не смешивать разные зоны ответственности, вынесли технические, финансовые и организационные пункты отдельно."
    ];
    const asks = [
      "Просим проверить исходные данные и отметить расхождения.",
      "Будем признательны за комментарии с указанием ответственного подразделения.",
      "Пожалуйста, подтвердите, можно ли использовать эту редакцию для следующего этапа согласования.",
      "Если замечаний нет, сообщите, кто сможет подтвердить переход к следующему шагу.",
      "Просим вернуть консолидированную позицию либо обозначить вопросы, требующие отдельного обсуждения."
    ];
    email.body = pick(openings, key + "|open") + " " +
      pick(body, key + "|body") + " " +
      pick(asks, key + "|ask") +
      " Предлагаемый срок ответа — " + due + ". Дата письма: " +
      dateRu(email.date) + ". С уважением, " + (email.manager || "проектная команда") + ".";
  }
}

function rewriteMeeting(meeting, people, seed, isDecision = false) {
  const key = seed + "|" + meeting.id;
  const topic = meeting.topic || meeting.agenda || "текущие вопросы проекта";
  const p = profile(topic);
  const ids = meeting.clientAttendeeIds || (meeting.personId ? [meeting.personId] : []);
  const attendees = ids.map(id => fullName(people, id));
  const attendeeText = attendees.length
    ? "В обсуждении со стороны клиента участвовали " + attendees.join(", ") + "."
    : "Состав участников указан в карточке встречи.";
  const opening = [
    "Рабочая встреча была посвящена теме «" + topic + "» и проверке текущего статуса.",
    "Участники рассмотрели варианты действий по направлению «" + topic + "».",
    "В ходе встречи сверили позиции подразделений и перечень открытых вопросов по теме «" + topic + "».",
    "Основной задачей встречи было определить условия перехода к следующему этапу по теме «" + topic + "».",
    "Стороны сопоставили текущие ограничения и предложенный план работ по направлению «" + topic + "»."
  ];
  const discussion = [
    "Подробно рассмотрели " + pick(p.evidence, key + "|d1") + ".",
    "Отдельно обсудили " + pick(p.evidence, key + "|d2") + " и связанные с ним зависимости.",
    "Участники запросили уточнения по вопросу «" + pick(p.evidence, key + "|d3") + "».",
    "В перечень проверки включили " + pick(p.evidence, key + "|d4") + "."
  ];
  const decision = [
    "Итоговое решение не принято: требуется заключение профильных подразделений.",
    "Согласован предварительный вариант, окончательное утверждение состоится после проверки.",
    "Участники подтвердили дальнейшую проработку без фиксации окончательных обязательств.",
    "Разногласия сохранены в протоколе; владельцы пунктов подготовят альтернативные предложения.",
    "Подтверждены только те условия, по которым у сторон есть достаточные исходные данные."
  ];
  const actions = [
    "Координатор соберет замечания и разошлет обновленный протокол.",
    "Ответственные подразделения представят комментарии к следующей контрольной дате.",
    "После получения заключений стороны повторно сверят график и условия реализации.",
    "Следующая встреча состоится после обмена обновленными документами.",
    "Каждый владелец направления подтвердит статус своего пункта отдельно."
  ];
  const conclusion = isDecision
    ? pick(p.decision, key + "|decision")
    : pick(decision, key + "|decision");
  meeting.minutes = [
    pick(opening, key + "|opening"),
    attendeeText,
    stance(meeting.sentiment, key + "|stance"),
    pick(discussion, key + "|discussion"),
    conclusion,
    pick(actions, key + "|actions"),
    "Дата встречи: " + dateRu(meeting.date) + "."
  ].join(" ");
}

function rewriteInternalMessage(message, people, seed) {
  const key = seed + "|" + message.id;
  const from = fullName(people, message.fromPersonId);
  const to = fullName(people, message.toPersonId);
  const p = profile(message.topic);
  const intents = [
    "запросил экспертную проверку",
    "передал замечания для согласования",
    "предложил подключить коллегу к оценке",
    "обозначил риск, требующий отдельного решения",
    "попросил сопоставить две альтернативы",
    "направил промежуточную позицию подразделения",
    "предложил вынести вопрос на уровень руководителей",
    "попросил подтвердить исходные допущения"
  ];
  const details = [
    "В центре внимания — " + pick(p.evidence, key + "|detail1") + ".",
    "Необходимо уточнить " + pick(p.evidence, key + "|detail2") + ".",
    "До общего ответа важно проверить " + pick(p.evidence, key + "|detail3") + ".",
    "Отдельно требуется позиция владельца по вопросу «" + pick(p.evidence, key + "|detail4") + "»."
  ];
  const outcomes = [
    "Просьба вернуть комментарии до общей встречи.",
    "После проверки результат нужно зафиксировать в проектном протоколе.",
    "Окончательное решение остается за ответственным руководителем.",
    "Если замечания подтвердятся, потребуется пересмотреть план работ.",
    "Пока это рабочая позиция, а не согласованное решение."
  ];
  message.summary = from + " " + pick(intents, key + "|intent") + " " + to +
    " по теме «" + message.topic + "». " +
    pick(details, key + "|details") + " " +
    pick(outcomes, key + "|outcome") +
    " Дата обмена: " + dateRu(message.date) + ".";
}

export function generateV3_2(crm, v1, seed = DEFAULT_SEED) {
  // Reuse v3.1 structural generation to preserve the normalized model.
  const generated = generateV3(crm, v1, seed);
  const bank = generated.bank;
  const people = new Map(
    crm.people.filter(p => p.companyId === "bank").map(p => [p.id, p])
  );

  for (const call of bank.calls || []) rewriteCall(call, people, seed);
  for (const email of bank.emails || []) rewriteEmail(email, people, seed);
  for (const meeting of bank.meetings || []) rewriteMeeting(meeting, people, seed, false);
  for (const meeting of bank.decisionMeetings || []) rewriteMeeting(meeting, people, seed, true);
  for (const message of bank.clientInternalMessages || []) rewriteInternalMessage(message, people, seed);

  bank.metadata = {
    ...bank.metadata,
    generatorVersion: "3.2.0",
    textGeneration: "scenario_composed_contextual",
    textQuality: "scenario_intent_role_and_event_context",
    seed,
    parentGeneratorVersion: "3.1.0",
    warning: "ALL DATA FICTIONAL. NOT REAL CLIENT ACTIVITY, FINANCE OR VALIDATED ML LABELS."
  };

  const errors = [];
  const ids = new Set();
  for (const key of [
    "calls", "emails", "meetings", "decisionMeetings",
    "clientInternalMessages", "eventIndex"
  ]) {
    for (const row of bank[key] || []) {
      if (!row.id) errors.push("Missing ID in " + key);
      if (key !== "eventIndex" && ids.has(row.id)) errors.push("Duplicate ID " + row.id);
      if (key !== "eventIndex") ids.add(row.id);
    }
  }
  for (const key of ["calls", "emails", "meetings"]) {
    for (const row of bank[key] || []) {
      const text = key === "calls"
        ? (row.transcript || []).map(x => x.text).join(" ")
        : key === "emails" ? row.body : row.minutes;
      if (!String(text || "").trim()) errors.push("Empty text: " + row.id);
      if (row.date > bank.metadata.asOf) errors.push("Future event: " + row.id);
    }
  }
  for (const row of bank.decisionMeetings || []) {
    if (!String(row.minutes || "").trim()) errors.push("Empty decision meeting: " + row.id);
  }
  for (const row of bank.clientInternalMessages || []) {
    if (!String(row.summary || "").trim()) errors.push("Empty internal message: " + row.id);
    if (row.fromPersonId === row.toPersonId) errors.push("Self-message: " + row.id);
  }
  if (errors.length) throw new Error(errors.slice(0, 30).join("; "));

  return { bank, groundTruth: generated.groundTruth };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const crm = JSON.parse(readFileSync(resolve(root, "src/data/crm.json"), "utf8"));
  const v1 = JSON.parse(readFileSync(resolve(root, "src/data/synthetic/bank_ml_v1.json"), "utf8"));
  const { bank, groundTruth } = generateV3_2(crm, v1);
  const bankPath = resolve(root, "src/data/synthetic/bank_ml_v3.json");
  const truthPath = resolve(root, "src/data/synthetic/bank_ml_v3_ground_truth.json");
  mkdirSync(dirname(bankPath), { recursive: true });
  writeFileSync(bankPath, JSON.stringify(bank, null, 2) + "\n", "utf8");
  writeFileSync(truthPath, JSON.stringify(groundTruth, null, 2) + "\n", "utf8");
  console.log("Generated bank_ml_v3.json", {
    generatorVersion: bank.metadata.generatorVersion,
    calls: bank.calls.length,
    emails: bank.emails.length,
    meetings: bank.meetings.length,
    decisionMeetings: bank.decisionMeetings.length,
    clientInternalMessages: bank.clientInternalMessages.length,
    eventIndex: bank.eventIndex.length
  });
}
