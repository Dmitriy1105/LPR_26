import assert from "node:assert/strict";
import { generateCommunications, validateCommunications } from "./scenario_communication_generator_v1.mjs";

const first = generateCommunications({ seed: 42, organizations: 5, dealsPerOrganization: 6 });
const second = generateCommunications({ seed: 42, organizations: 5, dealsPerOrganization: 6 });
const validation = validateCommunications(first);
assert.deepEqual(first, second, "same seed must reproduce identical communications");
assert.equal(validation.pass, true, validation.errors.join("; "));
assert.equal(first.organization_count, 5);
assert.equal(first.deal_count, 30);
assert.equal(first.communication_count, first.event_count);
assert.equal(first.communications.length, first.world.events.length);
assert.equal(new Set(first.communications.map(x => x.ID)).size, first.communications.length);
assert.equal(new Set(first.communications.map(x => x.SOURCE_EVENT_ID)).size, first.event_count);
assert.ok(first.communications.every(x => x.DESCRIPTION && x.SUBJECT && x.AUTHOR_ID && x.DEAL_ID));
const channelCounts = Object.fromEntries(["email", "call", "meeting"].map(channel =>
  [channel, first.communications.filter(item => item.CHANNEL === channel).length]));
assert.ok(channelCounts.email > 0 && channelCounts.call > 0 && channelCounts.meeting > 0);
assert.ok(first.communications.every(item => item.TYPE_ID === ({ email: 4, call: 2, meeting: 1 })[item.CHANNEL]));
const report = {
  status: "PASS",
  seed: first.seed,
  organizations: first.organization_count,
  deals: first.deal_count,
  source_events: first.event_count,
  communications: first.communication_count,
  channel_counts: channelCounts,
  linked_source_events: new Set(first.communications.map(x => x.SOURCE_EVENT_ID)).size,
  deterministic: true,
  validation
};
console.log(JSON.stringify(report, null, 2));
