import { generate, validate as validateWorld } from "./scenario_engine_v4.mjs";

export const COMMUNICATION_VERSION = "1.0.0";

const channels = {
  request_information: { typeId: 4, label: "email" },
  delegate: { typeId: 4, label: "email" },
  complete_task: { typeId: 2, label: "call" },
  review: { typeId: 1, label: "meeting" },
  recommend: { typeId: 4, label: "email" },
  object: { typeId: 4, label: "email" },
  revise: { typeId: 2, label: "call" },
  approve: { typeId: 1, label: "meeting" },
  reject: { typeId: 1, label: "meeting" },
  close: { typeId: 1, label: "meeting" }
};

const roleLabel = {
  director: "директор",
  finance_head: "руководитель финансового отдела",
  technical_head: "руководитель технического направления",
  procurement_head: "руководитель закупок",
  analyst: "технический эксперт",
  buyer: "инициатор закупки"
};

function stableChoice(eventId, choices) {
  let hash = 2166136261;
  for (const ch of eventId) hash = Math.imul(hash ^ ch.charCodeAt(0), 16777619);
  return choices[(hash >>> 0) % choices.length];
}

function renderText(event, actor, target, deal) {
  const actorRole = roleLabel[actor.role] || actor.role;
  const targetRole = target ? (roleLabel[target.role] || target.role) : "участники процесса";
  const subjects = {
    request_information: ["Запрос исходных данных", "Уточнение требований", "Данные для рассмотрения сделки"],
    delegate: ["Назначение технической проверки", "Поручение по экспертизе", "Проверка технических требований"],
    complete_task: ["Результат выполнения проверки", "Статус поручения", "Передача результатов экспертизы"],
    review: ["Рассмотрение материалов сделки", "Экспертная проверка", "Обсуждение условий сделки"],
    recommend: ["Рекомендация по сделке", "Экспертное заключение", "Предложение по дальнейшим действиям"],
    object: ["Возражение по условиям", "Замечания к предложению", "Необходима корректировка решения"],
    revise: ["Корректировка условий", "Доработка материалов", "Обновлённая версия предложения"],
    approve: ["Согласование сделки", "Решение по сделке", "Подтверждение согласования"],
    reject: ["Отказ по сделке", "Решение об отклонении", "Итог рассмотрения сделки"],
    close: ["Закрытие процесса", "Фиксация результата", "Итоги рассмотрения"]
  };
  const bodies = {
    request_information: [
      "Прошу предоставить исходные сведения и требования по сделке.",
      "Для начала рассмотрения направьте, пожалуйста, необходимые данные.",
      "Нужно уточнить исходные условия, чтобы передать вопрос на проверку."
    ],
    delegate: [
      "Прошу провести проверку в пределах вашей технической компетенции и вернуть заключение.",
      "Назначаю экспертную проверку требований. Зафиксируйте замечания и результат.",
      "Передаю материалы на техническую экспертизу; решение по сделке пока не принимается."
    ],
    complete_task: [
      "Проверка выполнена. Результаты и замечания переданы ответственному сотруднику.",
      "Завершил порученную проверку; выводы готовы для рассмотрения.",
      "Передаю результат экспертизы для следующего этапа согласования."
    ],
    review: [
      "Рассмотрены представленные материалы. Проверка завершена, можно переходить к следующему этапу.",
      "Обсудили условия и результаты экспертизы; фиксирую итог рассмотрения.",
      "Проверил материалы сделки и передаю заключение участникам процесса."
    ],
    recommend: [
      "По результатам проверки рекомендую продолжить рассмотрение сделки.",
      "Направляю экспертную рекомендацию для принятия решения уполномоченным сотрудником.",
      "Существенные замечания рассмотрены; предлагаю передать вопрос на согласование."
    ],
    object: [
      "Есть замечания к текущим условиям. До их устранения согласование продолжать не следует.",
      "Возражаю против представленного варианта; требуется корректировка условий.",
      "Прошу учесть выявленные риски и вернуть предложение на доработку."
    ],
    revise: [
      "Внёс корректировки по замечаниям и направляю обновлённые материалы.",
      "Доработка выполнена. Прошу повторно рассмотреть обновлённый вариант.",
      "Обновил предложение с учётом замечаний; материалы готовы к повторной проверке."
    ],
    approve: [
      "Согласование завершено. Решение принято в рамках предоставленных полномочий.",
      "Подтверждаю согласование сделки после рассмотрения необходимых материалов.",
      "Решение по сделке принято; зафиксируйте результат и переходите к закрытию процесса."
    ],
    reject: [
      "По результатам рассмотрения сделка отклонена. Зафиксируйте основания и завершите процесс.",
      "Не согласовываю представленный вариант; решение — отклонить сделку.",
      "Рассмотрение завершено отрицательным решением. Дальнейшее исполнение не требуется."
    ],
    close: [
      "Фиксирую итог процесса и закрываю текущий этап.",
      "Результат рассмотрения внесён в историю сделки; процесс завершён.",
      "Подтверждаю завершение процесса с зафиксированным результатом."
    ]
  };
  const subject = stableChoice(event.id, subjects[event.type] || ["Обновление по сделке"]);
  const body = stableChoice(event.id + ":body", bodies[event.type] || ["Направляю информацию по текущему этапу."]);
  const outcome = event.outcome ? " Итог: " + event.outcome + "." : "";
  return {
    subject: subject + " " + deal.id,
    description: body + " Сделка: " + deal.id + ". Отправитель: " + actorRole +
      (target ? ". Адресат: " + targetRole + "." : ". Адресат: участники процесса.") + outcome
  };
}

export function generateCommunications({ seed = 42, organizations = 5, dealsPerOrganization = 6 } = {}) {
  const world = generate({ seed, organizations, dealsPerOrganization });
  const validation = validateWorld(world);
  if (!validation.pass) throw new Error("Scenario Engine validation failed: " + validation.errors.join("; "));
  const people = new Map(world.people.map(person => [person.id, person]));
  const deals = new Map(world.deals.map(deal => [deal.id, deal]));
  const communications = world.events.map((event, index) => {
    const actor = people.get(event.actor_id);
    const target = event.target_id ? people.get(event.target_id) : null;
    const deal = deals.get(event.deal_id);
    if (!actor || !deal) throw new Error("Missing actor/deal reference for " + event.id);
    const channel = channels[event.type];
    if (!channel) throw new Error("No communication mapping for event type " + event.type);
    const rendered = renderText(event, actor, target, deal);
    return {
      ID: "ACT-" + String(index + 1).padStart(6, "0"),
      TYPE_ID: channel.typeId,
      CHANNEL: channel.label,
      SUBJECT: rendered.subject,
      DESCRIPTION: rendered.description,
      CREATED: event.occurred_at,
      AUTHOR_ID: actor.id,
      RESPONSIBLE_ID: target ? target.id : actor.id,
      OWNER_TYPE_ID: 2,
      OWNER_ID: deal.id,
      COMMUNICATIONS: [actor.id, ...(target ? [target.id] : [])],
      SOURCE_EVENT_ID: event.id,
      DEAL_ID: deal.id,
      ORGANIZATION_ID: event.org,
      EVENT_TYPE: event.type,
      PREVIOUS_EVENT_ID: event.previous_event_id
    };
  });
  return {
    version: COMMUNICATION_VERSION,
    synthetic: true,
    seed,
    source: "scenario_engine_v4",
    organization_count: world.organizations.length,
    deal_count: world.deals.length,
    event_count: world.events.length,
    communication_count: communications.length,
    world,
    communications
  };
}

export function validateCommunications(dataset) {
  const errors = [];
  const check = (condition, message) => { if (!condition) errors.push(message); };
  const events = new Map(dataset.world.events.map(event => [event.id, event]));
  const deals = new Map(dataset.world.deals.map(deal => [deal.id, deal]));
  const people = new Map(dataset.world.people.map(person => [person.id, person]));
  const ids = new Set();
  const sourceIds = new Set();
  for (const item of dataset.communications) {
    check(!ids.has(item.ID), "duplicate activity id " + item.ID);
    ids.add(item.ID);
    check(!sourceIds.has(item.SOURCE_EVENT_ID), "duplicate source event " + item.SOURCE_EVENT_ID);
    sourceIds.add(item.SOURCE_EVENT_ID);
    const event = events.get(item.SOURCE_EVENT_ID);
    check(!!event, "orphan source event " + item.SOURCE_EVENT_ID);
    check(!!deals.get(item.DEAL_ID) && item.DEAL_ID === event?.deal_id, "deal link mismatch " + item.ID);
    check(!!people.get(item.AUTHOR_ID) && item.AUTHOR_ID === event?.actor_id, "author attribution mismatch " + item.ID);
    check(item.RESPONSIBLE_ID === (event?.target_id || event?.actor_id), "recipient attribution mismatch " + item.ID);
    check([1, 2, 4].includes(item.TYPE_ID), "unsupported activity type " + item.ID);
    check(typeof item.SUBJECT === "string" && item.SUBJECT.trim().length > 0, "empty subject " + item.ID);
    check(typeof item.DESCRIPTION === "string" && item.DESCRIPTION.trim().split(/\s+/).length >= 5, "insufficient communication text " + item.ID);
    check(item.CREATED === event?.occurred_at, "communication timestamp differs from source event " + item.ID);
  }
  check(dataset.communications.length === dataset.world.events.length, "not every event rendered as a communication");
  check(sourceIds.size === dataset.world.events.length, "source event coverage incomplete");
  return { pass: errors.length === 0, errors };
}
