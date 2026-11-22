// Synthetic bank dataset v3.
// Keeps the normalized bank_ml_v2 schema and adds richer multi-party events.
// Run: node scripts/generate_synthetic_bank_v3.mjs
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { generateV2 } from "./generate_synthetic_bank_v2.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const AS_OF = "2026-11-21";

function isoDate(value) {
  return new Date(value + "T12:00:00Z").toISOString().slice(0, 10);
}
function addDays(value, days) {
  const d = new Date(value + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}
function dayDiff(a, b) {
  return Math.round((Date.parse(b + "T00:00:00Z") - Date.parse(a + "T00:00:00Z")) / 86400000);
}
function unique(values) {
  return [...new Set(values.filter(Boolean))];
}
function stablePick(values, index) {
  return values[((index % values.length) + values.length) % values.length];
}


// ---------------------------------------------------------------------------
// Contextual text diversification v3.1.
// Deterministic from event fields and seed; does not change schemas or counts.
// ---------------------------------------------------------------------------
function hashIndex(value, length) {
  let hash = 2166136261;
  for (const ch of String(value)) {
    hash ^= ch.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) % length;
}
function variant(values, key) {
  return values[hashIndex(key, values.length)];
}
function ruDate(value) {
  const [year, month, day] = String(value).slice(0, 10).split("-");
  return day + "." + month + "." + year;
}
function personName(peopleById, id) {
  return peopleById.get(id)?.name || "коллега";
}
function firstName(peopleById, id) {
  return personName(peopleById, id).split(/\s+/)[0];
}
function topicContext(topic) {
  const t = String(topic || "").toLowerCase();
  if (t.includes("бюджет")) return "лимиты финансирования, структуру затрат и порядок подтверждения расходов";
  if (t.includes("безопас")) return "требования защиты информации, модель угроз и порядок проверки";
  if (t.includes("договор")) return "условия договора, распределение обязательств и маршрут согласования";
  if (t.includes("миграц")) return "этапы переноса, окно переключения и критерии готовности";
  if (t.includes("график")) return "сроки этапов, зависимости работ и ответственных исполнителей";
  if (t.includes("поддерж")) return "уровень сервиса, время реакции и порядок эскалации";
  if (t.includes("техничес")) return "архитектуру решения, интеграционные ограничения и критерии приемки";
  return "объем работ, ограничения проекта и порядок принятия решения";
}
function positionText(sentiment, key) {
  const tone = String(sentiment || "").toLowerCase();
  const options = tone.includes("позит")
    ? [
        "В целом предложенный подход поддерживаем; просим отдельно зафиксировать условия перехода.",
        "Предложение выглядит приемлемым. Для продвижения нужны подтвержденные сроки и ответственные.",
        "Готовы продолжить проработку при условии документального подтверждения ключевых параметров.",
        "Существенных возражений по направлению нет, но остаются вопросы по реализации."
      ]
    : tone.includes("сдерж")
      ? [
          "Пока сохраняются вопросы по рискам и распределению ответственности.",
          "Окончательную позицию сформируем после проверки расчетов и технических условий.",
          "Для согласования не хватает подтверждений по срокам, затратам и критериям приемки.",
          "Есть замечания, которые необходимо закрыть до вынесения вопроса на следующий уровень."
        ]
      : [
          "Позиция пока не определена; требуется сопоставить альтернативы и уточнить исходные данные.",
          "Нужно получить дополнительные сведения, прежде чем подтверждать предложенный вариант.",
          "Вопрос оставлен открытым до получения расчетов и заключений профильных подразделений.",
          "Участник запросил пояснения по условиям и ожидает консолидированную информацию."
        ];
  return variant(options, key);
}
function diversifyCall(call, peopleById, seed) {
  const name = firstName(peopleById, call.personId);
  const context = topicContext(call.topic);
  const key = String(seed) + "|" + call.id;
  const openers = [
    "Добрый день, " + name + ". Возвращаюсь к обсуждению темы «" + call.topic + "».",
    name + ", здравствуйте. Хотел сверить текущий статус вопроса «" + call.topic + "».",
    "Добрый день, " + name + ". Связываюсь по итогам предыдущего обсуждения «" + call.topic + "».",
    name + ", добрый день. Предлагаю уточнить оставшиеся вопросы по направлению «" + call.topic + "»."
  ];
  const managerQuestions = [
    "Предлагаю пройтись по таким пунктам: " + context + ".",
    "Важно согласовать следующие аспекты: " + context + ".",
    "Для следующего шага нужно уточнить: " + context + ".",
    "Отдельно предлагаю проверить: " + context + "."
  ];
  const managerActions = [
    "Со своей стороны подготовим сводку и направим ее участникам.",
    "Я зафиксирую договоренности и передам материалы ответственным коллегам.",
    "После звонка отправим перечень открытых вопросов и проект дальнейшего плана.",
    "Подготовим обновленные материалы, чтобы предметно обсудить оставшиеся разногласия."
  ];
  const clientActions = [
    "Пожалуйста, приложите исходные расчеты и укажите, какие решения требуются от нашей стороны.",
    "Направьте краткое резюме, перечень допущений и возможные даты следующего обсуждения.",
    "Просьба отдельно отметить открытые вопросы и подразделения, от которых ожидается ответ.",
    "После получения материалов вернемся с комментариями и предложением по дальнейшим действиям."
  ];
  const outcome = positionText(call.sentiment, key + "|position");
  const disposition = {
    materials_requested: "По итогам разговора запрошены дополнительные материалы.",
    next_meeting: "Стороны договорились вынести вопрос на отдельную рабочую встречу.",
    clarification: "Зафиксирована необходимость уточнить исходные условия.",
    follow_up: "Договорились вернуться к вопросу после внутренней проверки."
  }[call.disposition] || "Следующий шаг будет определен после сверки информации.";
  call.transcript = [
    { speaker: "manager", text: variant(openers, key + "|open") },
    { speaker: "client", text: outcome + " " + variant(managerQuestions, key + "|question") },
    { speaker: "manager", text: disposition + " " + variant(managerActions, key + "|action") },
    { speaker: "client", text: variant(clientActions, key + "|client-action") }
  ];
}
function diversifyEmail(email, peopleById, seed) {
  const name = firstName(peopleById, email.personId);
  const fullName = personName(peopleById, email.personId);
  const context = topicContext(email.subject || email.topic);
  const key = String(seed) + "|" + email.id;
  const followUpDays = 3 + hashIndex(key + "|due", 9);
  const due = ruDate(addDays(email.date, followUpDays));
  if (email.direction === "incoming") {
    const openings = [
      "Добрый день. Получили ваше сообщение по вопросу «" + (email.subject || "проекта") + "».",
      "Здравствуйте. Возвращаемся с ответом по теме «" + (email.subject || "проекта") + "».",
      "Коллеги, добрый день. Изучили направленные материалы по вопросу «" + (email.subject || "проекта") + "».",
      "Добрый день. Благодарим за материалы и пояснения по теме «" + (email.subject || "проекта") + "»."
    ];
    const requests = [
      "Просим дополнительно раскрыть следующие пункты: " + context + ".",
      "Для подготовки позиции необходимы уточнения по направлениям: " + context + ".",
      "Просим приложить расчеты и пояснить, как предлагается закрыть вопросы: " + context + ".",
      "Будем признательны за отдельный ответ по следующим аспектам: " + context + "."
    ];
    email.body = variant(openings, key + "|opening") + " " +
      positionText(email.sentiment, key + "|position") + " " +
      variant(requests, key + "|request") + " " +
      variant([
        "После внутреннего рассмотрения направим консолидированные замечания.",
        "Ответственных коллег подключим после получения недостающей информации.",
        "Просим учесть эти вопросы при подготовке следующей версии материалов.",
        "К дальнейшему согласованию вернемся после проверки профильными подразделениями."
      ], key + "|closing") + " С уважением, " + fullName + ".";
  } else {
    const openings = [
      "Здравствуйте, " + name + "! Направляем обновленные материалы по теме «" + (email.subject || "проекта") + "».",
      "Добрый день, " + name + ". По итогам предыдущего контакта подготовили информацию по теме «" + (email.subject || "проекта") + "».",
      name + ", здравствуйте. Во вложении направляем уточнения по вопросу «" + (email.subject || "проекта") + "».",
      "Уважаемый(ая) " + name + ", направляем согласованную версию материалов по теме «" + (email.subject || "проекта") + "»."
    ];
    const requests = [
      "Просим проверить указанные параметры и прислать замечания.",
      "Будем признательны, если подтвердите корректность исходных условий.",
      "Просим обозначить ответственных за проверку и удобный срок обратной связи.",
      "Если потребуется, организуем короткую рабочую встречу для разбора открытых пунктов."
    ];
    email.body = variant(openings, key + "|opening") + " " +
      variant([
        "В документе отдельно отражены " + context + ".",
        "В обновленной версии учтены замечания по направлениям: " + context + ".",
        "Ключевые допущения и варианты решения сгруппированы по вопросам: " + context + ".",
        "Для удобства проверки вынесли отдельным разделом: " + context + "."
      ], key + "|context") + " " + variant(requests, key + "|request") +
      " Просим по возможности вернуться с ответом до " + due +
      ". С уважением, " + (email.manager || "проектная команда") + ".";
  }
}
function meetingMinutes(topic, date, attendeeIds, peopleById, key, sentiment = "нейтральный") {
  const names = attendeeIds.map(id => personName(peopleById, id));
  const participants = names.length
    ? "Со стороны клиента участвовали: " + names.join(", ") + "."
    : "Состав участников зафиксирован в карточке встречи.";
  const context = topicContext(topic);
  const openings = [
    "На встрече " + ruDate(date) + " рассмотрели вопрос «" + topic + "» и сверили текущее состояние работ.",
    "Рабочая встреча " + ruDate(date) + " была посвящена теме «" + topic + "» и оставшимся пунктам согласования.",
    "В ходе обсуждения " + ruDate(date) + " участники сопоставили текущие требования и предложенный план по теме «" + topic + "».",
    "На встрече " + ruDate(date) + " проверили статус направления «" + topic + "», распределение задач и условия перехода к следующему этапу.",
    "Участники встречи " + ruDate(date) + " рассмотрели варианты решения по теме «" + topic + "» и зафиксировали вопросы для дополнительной проработки."
  ];
  const issues = [
    "Отдельно разобрали " + context + ".",
    "Основная часть обсуждения касалась следующих аспектов: " + context + ".",
    "В перечень открытых вопросов включили: " + context + ".",
    "Проверили взаимосвязь требований: " + context + ".",
    "Участники запросили дополнительные пояснения по направлениям: " + context + "."
  ];
  const decisions = [
    "Решение по спорным пунктам перенесено до получения подтверждающих материалов.",
    "Договорились подготовить консолидированный перечень замечаний и назначить ответственных.",
    "Согласовали продолжение проработки; окончательное утверждение оставлено за профильными подразделениями.",
    "Зафиксировали предварительный вариант, который должен пройти техническую и финансовую проверку.",
    "Подтверждено движение по согласованным пунктам, остальные вопросы оставлены в работе."
  ];
  const actions = [
    "Следующий шаг — обмен обновленными документами и повторная сверка.",
    "Ответственные стороны должны представить комментарии до следующего контрольного обсуждения.",
    "Проектная команда подготовит сводку решений, рисков и открытых зависимостей.",
    "После получения заключений вопрос будет возвращен на совместное рассмотрение."
  ];
  return [
    variant(openings, key + "|opening"),
    participants,
    positionText(sentiment, key + "|position"),
    variant(issues, key + "|issues"),
    variant(decisions, key + "|decision"),
    variant(actions, key + "|actions")
  ].join(" ");
}
function diversifyAllText(bank, peopleById, seed) {
  for (const call of bank.calls || []) diversifyCall(call, peopleById, seed);
  for (const email of bank.emails || []) diversifyEmail(email, peopleById, seed);
  for (const meeting of bank.meetings || []) {
    meeting.minutes = meetingMinutes(
      meeting.topic, meeting.date, meeting.clientAttendeeIds || [meeting.personId],
      peopleById, String(seed) + "|" + meeting.id, meeting.sentiment || "нейтральный"
    );
  }
  for (const meeting of bank.decisionMeetings || []) {
    meeting.minutes = meetingMinutes(
      meeting.agenda, meeting.date, meeting.clientAttendeeIds || [],
      peopleById, String(seed) + "|" + meeting.id, "нейтральный"
    );
  }
  for (const message of bank.clientInternalMessages || []) {
    const from = personName(peopleById, message.fromPersonId);
    const to = personName(peopleById, message.toPersonId);
    const context = topicContext(message.topic);
    const key = String(seed) + "|" + message.id;
    const bodies = [
      from + " направил(а) " + to + " замечания по теме «" + message.topic + "». В первую очередь требуется проверить " + context + ". Просьба собрать позицию профильного подразделения и вернуть комментарии.",
      from + " обратился(лась) к " + to + " за экспертной оценкой вопроса «" + message.topic + "». В сообщении выделены " + context + ". До общего согласования необходимо сверить исходные допущения.",
      from + " предложил(а) подключить " + to + " к проработке темы «" + message.topic + "». Причина обращения — необходимость уточнить " + context + ". Результат проверки следует зафиксировать для участников проекта.",
      from + " сообщил(а) " + to + ", что по теме «" + message.topic + "» остаются открытые пункты. Требуется дополнительно рассмотреть " + context + " и определить, какие данные нужны для решения.",
      from + " передал(а) " + to + " промежуточную позицию по теме «" + message.topic + "». Отдельного подтверждения требуют " + context + ". До получения ответа окончательный вывод делать рано.",
      from + " попросил(а) " + to + " проверить материалы по теме «" + message.topic + "». Вопросы относятся к направлениям: " + context + ". После проверки стороны смогут согласовать дальнейший порядок действий."
    ];
    message.summary = variant(bodies, key) + " Дата обмена: " + ruDate(message.date) + ".";
  }
}

export function generateV3(crm, v1, seed = 20261122) {
  const bank = generateV2(crm, v1, seed);
  const people = crm.people.filter(p => p.companyId === "bank");
  const peopleById = new Map(people.map(p => [p.id, p]));
  const opportunitiesById = new Map(bank.opportunities.map(o => [o.id, o]));
  const templates = [
    "Участники обсудили критерии выбора решения и распределили дальнейшие действия.",
    "Стороны сверили технические ограничения, бюджетные условия и порядок согласования.",
    "Зафиксированы позиции подразделений; окончательное решение отложено до получения дополнительных материалов.",
    "Обсуждены замечания участников и необходимые проверки перед следующим этапом."
  ];

  // Expand participant lists on existing decision meetings. The original
  // fields and normalized record structure are preserved.
  for (let i = 0; i < bank.decisionMeetings.length; i++) {
    const meeting = bank.decisionMeetings[i];
    const opp = opportunitiesById.get(meeting.opportunityId);
    if (!opp) throw new Error("Unknown opportunity for " + meeting.id);

    const candidates = unique([
      opp.primaryPersonId,
      ...(opp.stakeholderIds || []),
      ...(meeting.clientAttendeeIds || [])
    ]).filter(id => peopleById.has(id));

    const desiredCount = Math.min(candidates.length, 2 + (i % 3));
    const ordered = [
      opp.primaryPersonId,
      ...candidates.filter(id => id !== opp.primaryPersonId)
    ];
    const attendees = unique(ordered).slice(0, desiredCount);
    if (attendees.length < 2) {
      throw new Error("Decision meeting must have at least two client attendees: " + meeting.id);
    }

    meeting.clientAttendeeIds = attendees;
    meeting.minutes = templates[i % templates.length] +
      (meeting.minutes ? " " + meeting.minutes : "");
    meeting.synthetic = true;
  }

  // Add one additional internal client message per opportunity. It uses the
  // existing clientInternalMessages record schema and does not alter REST
  // response field names.
  const extraMessages = [];
  for (let i = 0; i < bank.opportunities.length; i++) {
    const opp = bank.opportunities[i];
    const ids = unique([...(opp.stakeholderIds || []), opp.primaryPersonId])
      .filter(id => peopleById.has(id));
    if (ids.length < 2) continue;

    const fromPersonId = stablePick(ids, i);
    let toPersonId = stablePick(ids, i + 1);
    if (toPersonId === fromPersonId) toPersonId = stablePick(ids, i + 2);
    if (toPersonId === fromPersonId) continue;

    const createdDate = opp.createdDate || AS_OF;
    const maxDays = Math.max(1, dayDiff(createdDate, opp.closedDate || AS_OF));
    const date = addDays(createdDate, Math.floor(maxDays * (0.35 + (i % 4) * 0.1)));
    if (date > AS_OF) throw new Error("Generated future internal message " + opp.id);

    extraMessages.push({
      id: "internal-v3-" + opp.id,
      companyId: "bank",
      opportunityId: opp.id,
      date,
      fromPersonId,
      toPersonId,
      channel: ["internal_email", "meeting_note", "internal_chat"][i % 3],
      topic: ["Проверка требований", "Бюджет и условия", "Согласование решения", "Риски внедрения"][i % 4],
      summary: [
        "Участники обменялись замечаниями и договорились о дополнительной проверке.",
        "Коллеги обсудили ограничения и определили, какие сведения нужны для решения.",
        "Зафиксированы разные позиции подразделений; требуется согласование.",
        "Один участник рекомендовал подключить коллегу с профильной компетенцией."
      ][i % 4],
      synthetic: true
    });
  }
  bank.clientInternalMessages.push(...extraMessages);

  // Diversify all customer-facing and internal event text without changing schemas/counts.
  diversifyAllText(bank, peopleById, seed);

  // Keep eventIndex synchronized with the expanded attendee lists.
  const eventBySourceId = new Map(bank.eventIndex.map(e => [e.sourceId, e]));
  for (const meeting of bank.decisionMeetings) {
    const event = eventBySourceId.get(meeting.id);
    if (event) event.personIds = unique(meeting.clientAttendeeIds);
  }
  for (const message of extraMessages) {
    bank.eventIndex.push({
      id: "event-" + message.id,
      sourceId: message.id,
      kind: "client_internal",
      date: message.date,
      companyId: "bank",
      personIds: unique([message.fromPersonId, message.toPersonId]),
      opportunityId: message.opportunityId,
      synthetic: true
    });
  }
  bank.eventIndex.sort((a, b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id));

  bank.metadata = {
    ...bank.metadata,
    dataset: "lpr_bank_synthetic_v3",
    version: 3,
    seed,
    asOf: AS_OF,
    parentDataset: "lpr_bank_synthetic_v2",
    compatibility: "normalized_v2_schema_additive_records",
    generatorVersion: "3.1.0",
    textGeneration: "deterministic_contextual_variants",
    textQuality: "event_specific_nonboilerplate",
    warning: "ALL DATA FICTIONAL. NOT REAL CLIENT ACTIVITY, FINANCE OR VALIDATED ML LABELS."
  };

  const allPeopleIds = new Set(people.map(p => p.id));
  const errors = [];
  const allRecordIds = new Set();
  for (const key of ["decisionMeetings", "clientInternalMessages", "eventIndex"]) {
    for (const row of bank[key] || []) {
      if (!row.id) errors.push("Missing ID in " + key);
      if (allRecordIds.has(row.id) && key !== "eventIndex") errors.push("Duplicate generated ID " + row.id);
      allRecordIds.add(row.id);
    }
  }
  for (const meeting of bank.decisionMeetings) {
    const ids = unique(meeting.clientAttendeeIds || []);
    if (ids.length < 2) errors.push("Meeting has fewer than two client participants: " + meeting.id);
    for (const id of ids) if (!allPeopleIds.has(id)) errors.push("Unknown meeting participant " + id);
  }
  for (const message of bank.clientInternalMessages) {
    if (message.fromPersonId === message.toPersonId) errors.push("Self-message " + message.id);
    for (const id of [message.fromPersonId, message.toPersonId]) {
      if (!allPeopleIds.has(id)) errors.push("Unknown message participant " + id);
    }
  }
  for (const event of bank.eventIndex) {
    for (const id of event.personIds || []) if (!allPeopleIds.has(id)) errors.push("Unknown event participant " + id);
  }
  if (errors.length) throw new Error(errors.slice(0, 20).join("; "));

  const groundTruth = {
    synthetic: true,
    dataset: "lpr_bank_synthetic_v3_ground_truth",
    version: 3,
    warning: "EVALUATION ONLY. MUST NOT BE USED AS NLP INPUT FEATURES OR INFERENCE CONTEXT.",
    excludedFromNlpInputs: true,
    participantTruth: [
      ...bank.decisionMeetings.map(m => ({
        sourceId: m.id, eventType: "decision_meeting",
        participantContactIds: unique(m.clientAttendeeIds),
        expectedParticipantCount: unique(m.clientAttendeeIds).length
      })),
      ...bank.clientInternalMessages.map(m => ({
        sourceId: m.id, eventType: "client_internal",
        participantContactIds: unique([m.fromPersonId, m.toPersonId]),
        senderContactId: m.fromPersonId,
        recipientContactId: m.toPersonId
      }))
    ],
    roleTruth: people.map(p => ({
      contactId: p.id,
      decisionRole: p.decisionRole,
      department: p.department,
      title: p.title
    })),
    organizationalRelationTruth: crm.relations
      .filter(r => r.companyId === "bank")
      .map(r => ({
        relationId: r.id, sourceContactId: r.from,
        targetContactId: r.to, relationType: r.type,
        source: "CRM_SYNTHETIC_GROUND_TRUTH"
      }))
  };

  return { bank, groundTruth };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const crm = JSON.parse(readFileSync(resolve(root, "src/data/crm.json"), "utf8"));
  const v1 = JSON.parse(readFileSync(resolve(root, "src/data/synthetic/bank_ml_v1.json"), "utf8"));
  const { bank, groundTruth } = generateV3(crm, v1);
  const bankPath = resolve(root, "src/data/synthetic/bank_ml_v3.json");
  const truthPath = resolve(root, "src/data/synthetic/bank_ml_v3_ground_truth.json");
  mkdirSync(dirname(bankPath), { recursive: true });
  writeFileSync(bankPath, JSON.stringify(bank, null, 2) + "\n", "utf8");
  writeFileSync(truthPath, JSON.stringify(groundTruth, null, 2) + "\n", "utf8");
  console.log("Generated bank_ml_v3.json", {
    opportunities: bank.opportunities.length,
    decisionMeetings: bank.decisionMeetings.length,
    clientInternalMessages: bank.clientInternalMessages.length,
    multiParticipantMeetings: bank.decisionMeetings.filter(m => new Set(m.clientAttendeeIds).size >= 2).length,
    groundTruthParticipants: groundTruth.participantTruth.length
  });
}
