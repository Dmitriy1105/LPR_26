# Generator v4.0 Architecture & Data Quality Audit — Initial Defect Register

**Branch:** `feature/generator-v4-organization-engine`  
**Audit basis:** committed source and reports on the branch head at audit start  
**Status:** REVIEW_REQUIRED  
**Scope:** synthetic Generator v4.0 only. NLP remains a separate downstream analysis system.

This is an evidence-based initial register. A passing CI means the audit script ran and detected the current state; it does not mean Generator v4.0 passed acceptance.

| ID | Severity | Status | Finding | Evidence / impact |
|---|---|---|---|---|
| GEN-001 | CRITICAL | CLOSED | Scenario Engine authority enforcement | Dedicated regression on CI #160: valid seed=42 scenario passes; unauthorized actor, expired grant, future grant, wrong-scope grant and wrong-organization grant are all rejected (1 positive + 5 negative cases). The legacy smoke `negative_test.pass=false` records the validator rejecting a deliberately unauthorized event; it was not evidence of a failed test. |
| GEN-002 | HIGH | OPEN | E2E does not execute the v4 scenario/BPMN runtime | `scripts/generator_v4_e2e_v1.py` validates organization modules and stored REST fixtures but does not call `scenario_engine_v4.mjs`, `process_executor_v4.py` or `authority_execution_v1.py`. Its PASS is not a full process-to-dataset E2E result. |
| GEN-003 | HIGH | OPEN | Scenario Engine does not produce CRM communication projections | `scripts/scenario_engine_v4.mjs` returns organizations, people, grants, deals and events; it does not generate activity/email/call/meeting records or communication text. |
| GEN-004 | HIGH | OPEN | v4 scenario output lacks scenario-linked Ground Truth | The scenario output has no gold event/label projection, although the proposed v4 Data Contract defines gold events and attribution provenance as a distinct layer. |
| GEN-005 | HIGH | OPEN | Fixture total does not match the documented regression target | The v4 Data Contract says preserve 767 records; the committed REST manifest sums to 677 (1 company + 30 contacts + 18 deals + 44 invoices + 540 activities + 44 tasks). The target and fixture version must be reconciled explicitly. |
| GEN-006 | HIGH | OPEN | Generator v4 Data Contract is not approved | `docs/GENERATOR_V4_DATA_CONTRACT.md` is marked `PROPOSAL_REVIEW_REQUIRED`; output schema and acceptance gates are not authoritative yet. |
| GEN-007 | HIGH | OPEN | Previous architecture defects remain partial | `reports/architecture_defect_registry.json` still has ARCH-004/005/006/011/013/014/015 in PARTIAL status. These are carried forward, not duplicated as new GEN IDs. |
| GEN-008 | MEDIUM | DECISION_REQUIRED | BPMN/DMN runtime is a restricted custom profile | ARCH-012 remains a LIMITATION; the ADR explicitly says initial models are descriptive and not executable-certified. Do not claim general OMG BPMN/DMN conformance. |
| GEN-009 | MEDIUM | DECISION_REQUIRED | BPMN definitions are declared non-executable | The inspected BPMN process definitions use `isExecutable="false"`; they are currently inputs to a custom restricted runner, not standalone executable BPMN models. |

## Audit interpretation

- Existing organization baseline PASS is valid only for the structural checks listed in `docs/ORGANIZATION_ENGINE_BASELINE_V1.md`.
- Existing Process Model QC PASS is valid only for the scripts and fixtures it runs.
- The current Generator v4 smoke report has a failed negative authorization gate.
- The current E2E test is not end-to-end across BPMN/DMN, scenario generation, communication rendering, and Ground Truth.
- NLP is intentionally outside the generator execution path. It will consume the released synthetic dataset and compare predictions with separately held Ground Truth.

## Remediation order

1. GEN-001: CLOSED on CI #160. Valid scenario passes; five unauthorized/invalid-grant mutations are rejected.
2. GEN-006: approve the v4 Data Contract and settle the 767-record baseline/versioning rule.
3. GEN-002 and GEN-007: connect the authoritative BPMN/DMN execution boundary to scenario generation; close carried architecture defects.
4. GEN-003 and GEN-004: add CRM projections and Ground Truth as separate outputs derived from the same hidden scenario state.
5. GEN-005: regenerate/version fixtures to match the approved baseline and verify all references/counts.
6. GEN-008 and GEN-009: document the supported BPMN/DMN profile and decide whether full executable BPMN conformance is required for v4.0.
7. Run a genuine full E2E audit, diversity/realism audit, negative tests, deterministic replay and release gate.

No defect is marked closed by this initial audit. GEN-008 and GEN-009 are architecture-scope decisions, not assumed implementation defects: confirm whether the project requires a restricted custom BPMN/DMN profile or executable-standard model files. Close each item only with a code change, a focused regression test, and a passing CI run on the exact commit.
