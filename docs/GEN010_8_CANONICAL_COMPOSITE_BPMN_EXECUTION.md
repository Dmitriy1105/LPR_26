# GEN-010.8 — Canonical Composite BPMN Execution

**Status:** PASS — recursive composite execution and regression suite completed in GitHub Actions  
**Branch:** `feature/generator-v4-organization-engine`

## Delivered

- `scripts/process_executor_composite_v1.py`: bounded recursive BPMN executor for registered `callActivity` nodes, child input/output mappings, nested traces, DMN decisions and named process hooks.
- `scripts/generator_v4_composite_bpmn_audit_v1.py`: in-memory execution of `corporate_multilevel_universal` for the canonical v4 scenario world.
- `scripts/test_generator_v4_composite_bpmn_audit_v1.py`: regression tests for all-deal execution, nested calls, authority checks, conflict/revision routing, event closure and generation safeguards.
- `models/process_registry.json`: final deal subprocess now receives explicit `dealRequirementsMet` and `revisionAllowed` inputs, allowing the exact conflict/revision scenario to follow the BPMN revision branch.
- `.github/workflows/process-model-qc.yml`: composite audit and tests added to the process-model CI pipeline.

## Verification scope

The QC world is rebuilt in memory using seed 42. The composite root calls technical expertise, budget escalation (which itself calls budget approval), the readiness DMN decision and the final deal approval subprocess.

The regression suite verifies:
- 800 composite process executions;
- 200 conflict/revision episodes follow the revision path and reach approval;
- 120 rejected episodes reach the rejection outcome;
- 240 recorded unit-approval events resolve to their exact time-valid authority grants;
- 800 final decision events identify the authorized final actor;
- 800 closure events agree with the canonical deal outcome;
- generation remains disabled.

## Important limitation — financial policy evidence

The current canonical v4 organization/scenario contract does not yet contain financial authority bands, deal amounts, currency, or a complete funds-availability evidence model. Consequently, the budget subprocess is exercised with explicit synthetic scenario inputs. The finance actor's unit-level authority grant is checked, but this must **not** be interpreted as validation of a monetary approval limit or a real financial authority policy.

A dedicated financial-authority data contract and evidence-backed budget grants are required before budget decisions can be considered fully grounded. This is a tracked gap, not a PASS claim.

## Remaining boundary

This stage executes the nested process model and checks final/unit decision attribution and closure. It does not yet establish full one-to-one semantic equivalence between every BPMN task and every event in the journal, nor does it render or validate natural-language email/call/meeting texts. Those are separate validation workstreams.

## Generation safeguard

No persistent CRM fixture or NLP corpus was written. `generation_authorized=false` and `bulk_generation_enabled=false` remain unchanged.

## Next stage — GEN-010.9

Build the canonical communication renderer. It must produce distinct observable emails, call records and meeting notes from event context, retain source/event/author/participant/addressee lineage, preserve observable missingness, and keep hidden Ground Truth out of model-facing text. Validate semantic entailment and text diversity before any bulk-generation authorization.
