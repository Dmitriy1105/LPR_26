import assert from "node:assert/strict";
import { generate, validate } from "./scenario_engine_v4.mjs";

const base = generate({ seed: 42, organizations: 5, dealsPerOrganization: 6 });
const baseline = validate(base);
const cases = [];

function expectRejected(name, mutate, expectedText = "unauthorized decision") {
  const world = structuredClone(base);
  const decision = world.events.find(e => e.type === "approve" || e.type === "reject");
  assert.ok(decision, "fixture must contain a decision");
  mutate(world, decision);
  const result = validate(world);
  assert.equal(result.pass, false, name + " must be rejected");
  assert.ok(result.errors.some(e => e.includes(expectedText)), name + " must fail for " + expectedText + "; got " + result.errors.join("; "));
  cases.push({ name, rejected: true });
}

const positive = baseline.pass;
if (!positive) {
  // Preserve diagnostics in the report; assertions below fail the workflow with the exact errors.
}

expectRejected("actor_without_scope_grant", (w, d) => {
  d.actor_id = w.people.find(p => p.org === d.org && p.role === "buyer").id;
});
expectRejected("expired_scope_grant", (w, d) => {
  const g = w.grants.find(x => x.person_id === d.actor_id && x.org === d.org && x.scope === d.scope);
  assert.ok(g, "decision actor must have a matching grant in baseline");
  g.valid_to = d.occurred_at.slice(0, 10);
});
expectRejected("future_scope_grant", (w, d) => {
  const g = w.grants.find(x => x.person_id === d.actor_id && x.org === d.org && x.scope === d.scope);
  assert.ok(g, "decision actor must have a matching grant in baseline");
  g.valid_from = "2099-01-01";
});
expectRejected("wrong_scope_grant", (w, d) => {
  const g = w.grants.find(x => x.person_id === d.actor_id && x.org === d.org && x.scope === d.scope);
  assert.ok(g, "decision actor must have a matching grant in baseline");
  g.scope = "unrelated_scope";
});
expectRejected("wrong_org_grant", (w, d) => {
  const g = w.grants.find(x => x.person_id === d.actor_id && x.org === d.org && x.scope === d.scope);
  assert.ok(g, "decision actor must have a matching grant in baseline");
  g.org = "ORG-999";
});

const report = {
  status: positive && cases.length === 5 ? "PASS" : "FAIL",
  baseline: { pass: baseline.pass, errors: baseline.errors },
  positive_cases: 1,
  negative_cases: cases.length,
  negative_cases_passed: cases.filter(x => x.rejected).length,
  cases
};
console.log(JSON.stringify(report));
assert.equal(positive, true, "valid generated scenario must pass authority validation: " + baseline.errors.join("; "));
assert.equal(cases.length, 5);
