// Bitrix24 REST-compatible fixtures for synthetic bank dataset v3.
// REST response contract remains unchanged: crm.item.list,
// crm.activity.list and tasks.task.list legacy response shapes.
// Run: node scripts/generate_bitrix24_contract_fixtures_v2.mjs
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const iso = (d, t = "12:00:00") => d ? d + "T" + t + "+03:00" : null;
const plusMinutes = (d, t, minutes) => {
  const parts = t.split(":").map(Number);
  const yearParts = d.split("-").map(Number);
  const z = new Date(Date.UTC(yearParts[0], yearParts[1] - 1, yearParts[2], parts[0], parts[1], parts[2] || 0));
  z.setUTCMinutes(z.getUTCMinutes() + minutes);
  return z.toISOString().slice(0, 19) + "+03:00";
};
const unique = values => [...new Set(values.filter(Boolean))];

export function generateFixturesV2(crm, bank) {
  const company = crm.companies.find(c => c.id === "bank");
  const people = crm.people.filter(p => p.companyId === "bank");
  if (!company || people.length !== 30 || bank.metadata.companyId !== "bank" || bank.metadata.version !== 3) {
    throw new Error("Dataset mismatch: expected bank synthetic v3");
  }

  const managers = [...new Set(people.map(p => p.owner))].sort();
  const users = Object.fromEntries(managers.map((m, i) => [m, 17 + i]));
  const contactIds = Object.fromEntries(people.map((p, i) => [p.id, 1001 + i]));
  const dealIds = Object.fromEntries(bank.opportunities.map((o, i) => [o.id, 2001 + i]));
  const invoiceIds = Object.fromEntries(bank.invoices.map((x, i) => [x.id, 4001 + i]));
  const taskIds = Object.fromEntries(bank.crmTasks.map((x, i) => [x.id, 9001 + i]));
  const emailByContact = Object.fromEntries(people.map(p => [p.id, p.id + "@client.example"]));
  const personIdFromAddress = value => {
    const match = String(value || "").match(/(bank-p\d+)@client\.example/i);
    return match && contactIds[match[1]] ? match[1] : null;
  };

  const companies = [{
    id: 42, title: company.name, comments: company.description,
    assignedById: users[people[0].owner]
  }];
  const contacts = people.map(p => ({
    id: contactIds[p.id],
    name: p.name.split(" ")[0],
    lastName: p.name.split(" ").slice(1).join(" "),
    post: p.title, companyId: 42,
    assignedById: users[p.owner], typeId: "CLIENT"
  }));
  const deals = bank.opportunities.map(o => ({
    id: dealIds[o.id],
    title: company.initiative + " — " + o.id,
    companyId: 42,
    contactIds: o.stakeholderIds.map(x => contactIds[x]).filter(Boolean),
    assignedById: users[o.manager],
    stageId: o.stage === "won" ? "WON" : o.stage === "lost" ? "LOSE" : "NEW",
    closed: ["won", "lost"].includes(o.stage),
    opportunity: o.estimatedAmountRub, currencyId: "RUB",
    begindate: o.createdDate, closedate: o.closedDate || null
  }));
  const invoices = bank.invoices.map(x => ({
    id: invoiceIds[x.id], title: "Счёт " + x.id,
    accountNumber: x.id, companyId: 42,
    opportunity: x.amountRub, currencyId: x.currency || "RUB",
    createdTime: iso(x.issuedDate)
  }));

  const activityRecords = [];
  const addActivity = spec => {
    const ids = unique(spec.participantIds).filter(id => contactIds[id]);
    if (!ids.length) throw new Error("Activity " + spec.sourceId + " has no mapped contact");
    const owner = ids[0];
    const communications = ids.map(id => ({
      ENTITY_ID: String(contactIds[id]),
      ENTITY_TYPE_ID: "3",
      ...(spec.kind === "email" ? {
        TYPE: "EMAIL",
        VALUE: (spec.emailValues && spec.emailValues[id]) || emailByContact[id]
      } : spec.kind === "call" ? { TYPE: "PHONE" } : {})
    }));
    const id = 5001 + activityRecords.length;
    activityRecords.push({
      ID: String(id),
      OWNER_ID: String(contactIds[owner]),
      OWNER_TYPE_ID: "3",
      TYPE_ID: spec.kind === "call" ? "2" : spec.kind === "email" ? "4" : "1",
      SUBJECT: spec.subject,
      DESCRIPTION: spec.description,
      DESCRIPTION_TYPE: "1",
      START_TIME: iso(spec.date, spec.time || "12:00:00"),
      END_TIME: plusMinutes(spec.date, spec.time || "12:00:00", spec.duration || 5),
      RESPONSIBLE_ID: String(users[spec.manager] || users[people[0].owner]),
      COMPLETED: "Y",
      ...(spec.direction ? { DIRECTION: spec.direction } : {}),
      COMMUNICATIONS: communications
    });
  };

  for (const x of bank.calls) {
    addActivity({
      sourceId: x.id, kind: "call", date: x.date,
      time: String(x.startTime || "12:00").padStart(5, "0") + ":00",
      duration: x.durationMinutes || 5,
      participantIds: [x.personId],
      subject: "Звонок: " + x.topic,
      description: "Тема звонка: " + x.topic + "\n" +
        (x.transcript || []).map(t => t.speaker + ": " + t.text).join("\n"),
      manager: x.manager, direction: "2"
    });
  }
  for (const x of bank.emails) {
    const participants = unique([x.personId, personIdFromAddress(x.from), personIdFromAddress(x.to)]);
    const emailValues = Object.fromEntries(participants.map(id => [id, emailByContact[id]]));
    addActivity({
      sourceId: x.id, kind: "email", date: x.date,
      participantIds: participants, subject: x.subject,
      description: x.body, manager: x.manager,
      direction: x.direction === "incoming" ? "1" : "2", emailValues
    });
  }
  for (const x of bank.meetings) {
    addActivity({
      sourceId: x.id, kind: "meeting", date: x.date,
      duration: x.durationMinutes || 45,
      participantIds: x.clientAttendeeIds || [x.personId],
      subject: "Встреча: " + x.topic,
      description: x.minutes, manager: x.manager
    });
  }

  // These enriched multi-party events are mapped into the same standard
  // legacy REST crm.activity.list fields and COMMUNICATIONS references.
  for (const x of bank.decisionMeetings || []) {
    const opp = bank.opportunities.find(o => o.id === x.opportunityId);
    addActivity({
      sourceId: x.id, kind: "meeting", date: x.date,
      duration: 45, participantIds: x.clientAttendeeIds,
      subject: "Встреча по решению: " + x.agenda,
      description: x.minutes, manager: opp && opp.manager
    });
  }
  for (const x of bank.clientInternalMessages || []) {
    const opp = bank.opportunities.find(o => o.id === x.opportunityId);
    const participantIds = unique([x.fromPersonId, x.toPersonId]);
    addActivity({
      sourceId: x.id, kind: "email", date: x.date, duration: 5,
      participantIds,
      subject: "Внутреннее обсуждение: " + x.topic,
      description: x.summary,
      manager: opp && opp.manager,
      emailValues: Object.fromEntries(participantIds.map(id => [id, emailByContact[id]]))
    });
  }

  const tasks = bank.crmTasks.filter(t => t.status !== "cancelled").map(t => ({
    id: String(taskIds[t.id]),
    title: t.taskType === "follow_up" ? "Связаться с клиентом" : "Согласовать дальнейшие действия",
    description: "Задача по клиенту " + company.name,
    createdDate: iso(t.createdDate), deadline: iso(t.dueDate),
    closedDate: iso(t.completedDate),
    responsibleId: String(users[t.manager]),
    status: t.status === "completed" ? "5" : "2",
    ufCrmTask: ["C_" + contactIds[t.personId]].concat(
      t.opportunityId ? ["D_" + dealIds[t.opportunityId]] : []
    )
  }));

  const defs = [
    ["companies", "crm.item.list", 4, "result.items", companies],
    ["contacts", "crm.item.list", 3, "result.items", contacts],
    ["deals", "crm.item.list", 2, "result.items", deals],
    ["invoices", "crm.item.list", 31, "result.items", invoices],
    ["activities", "crm.activity.list", null, "result", activityRecords],
    ["tasks", "tasks.task.list", null, "result.tasks", tasks]
  ];
  const pages = {}, methods = [];
  for (const [key, method, entityTypeId, resultPath, rows] of defs) {
    const pageInfo = [];
    for (let i = 0; i < rows.length; i += 50) {
      const file = key + "/page_" + String(i / 50 + 1).padStart(3, "0") + ".json";
      const items = rows.slice(i, i + 50);
      pages[file] = {
        result: resultPath === "result.items" ? { items } :
          resultPath === "result.tasks" ? { tasks: items } : items,
        total: rows.length,
        ...(i + 50 < rows.length ? { next: i + 50 } : {})
      };
      pageInfo.push({ start: i, file, count: items.length });
    }
    methods.push({
      key, method, ...(entityTypeId ? { entityTypeId } : {}),
      resultPath, recordCount: rows.length, pages: pageInfo,
      requestExample: {
        method,
        params: {
          ...(entityTypeId ? { entityTypeId } : {}),
          ...(method === "crm.item.list" ? { select: ["*"], order: { id: "ASC" } } :
            method === "crm.activity.list" ? { select: ["*", "COMMUNICATIONS"], order: { ID: "ASC" } } :
              { select: ["ID", "TITLE", "DESCRIPTION", "STATUS", "CREATED_DATE", "DEADLINE", "CLOSED_DATE", "RESPONSIBLE_ID", "UF_CRM_TASK"], order: { ID: "asc" } }),
          start: 0
        }
      }
    });
  }

  const errors = {
    access_denied: { error: "ACCESS_DENIED", error_description: "Access denied" },
    insufficient_scope: { error: "insufficient_scope", error_description: "The request requires higher privileges than those provided by the access token" },
    invalid_credentials: { error: "INVALID_CREDENTIALS", error_description: "Invalid request credentials" }
  };
  const multiPartyActivities = activityRecords.filter(a => a.COMMUNICATIONS.length >= 2);
  const manifest = {
    synthetic: true, profile: "legacy-rest-v1", apiBase: "/rest/",
    snapshotDate: bank.metadata.asOf, docsChecked: "2026-11-21",
    pageSize: 50, timezone: "+03:00",
    sources: ["src/data/crm.json", "src/data/synthetic/bank_ml_v3.json"],
    recordCounts: Object.fromEntries(defs.map(x => [x[0], x[4].length])),
    multiPartyActivityCount: multiPartyActivities.length,
    multiPartyCommunicationReferences: multiPartyActivities.reduce((n, a) => n + a.COMMUNICATIONS.length, 0),
    methods, errors: Object.keys(errors),
    excluded: ["manualAnnotations", "relationshipEvents", "personSnapshots", "opportunitySnapshots", "payments", "receivables", "contracts"],
    limitations: [
      "Synthetic fixtures, not captured from a real portal",
      "Subset of standard legacy REST fields",
      "Saved response pages, not a live REST server",
      "No authorization or access filtering",
      "Internal client messages are represented as illustrative email activities",
      "This is legacy REST v1 response shape, not REST 3.0"
    ]
  };
  const mapping = {
    synthetic: true, companyIds: { bank: 42 }, contactIds, dealIds, invoiceIds,
    activityIds: Object.fromEntries(activityRecords.map(a => [a.ID, Number(a.ID)])),
    taskIds, users
  };
  return { manifest, mapping, pages, errors, activityRecords };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const crm = JSON.parse(readFileSync(resolve(root, "src/data/crm.json"), "utf8"));
  const bank = JSON.parse(readFileSync(resolve(root, "src/data/synthetic/bank_ml_v3.json"), "utf8"));
  const out = resolve(root, "src/data/bitrix24_contract_v2");
  const generated = generateFixturesV2(crm, bank);
  for (const [name, value] of [
    ["manifest.json", generated.manifest],
    ["id_mapping.json", generated.mapping],
    ...Object.entries(generated.pages),
    ...Object.entries(generated.errors).map(([name, obj]) => ["errors/" + name + ".json", obj])
  ]) {
    const path = resolve(out, name);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, JSON.stringify(value, null, 2) + "\n", "utf8");
  }
  console.log("Generated Bitrix24 REST-compatible fixtures v2", generated.manifest.recordCounts);
}
