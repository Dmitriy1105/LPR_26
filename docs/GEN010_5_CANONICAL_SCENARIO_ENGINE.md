# GEN-010.5 — Canonical Scenario Engine v4.0

**Status:** PASS — full-contract in-memory QC  
**Tested commit:** `c2f61781c4f8eae555b7052317e9e981424a2131`  
**Workflow:** [Process model QC #45485343408](https://github.com/Dmitriy1105/LPR_26/actions/runs/45485343408)  
**Branch:** `feature/generator-v4-organization-engine`

## Delivered

- `scripts/generator_v4_scenario_engine_v1.py` — canonical scenario builder consuming the existing 20-organization v4 adapter output.
- `scripts/test_generator_v4_scenario_engine_v1.py` — full-contract, reproducibility, missingness, authority-reference and negative configuration tests.
- Updated `.github/workflows/process-model-qc.yml` to execute the engine and retain its JSON report and test output.

## Full-contract in-memory result

| Requirement | QC result |
|---|---:|
| Organizations | 20 |
| Deals | 800 |
| Employees per organization | variable, 30–40 |
| Routine approval | exactly 400 |
| Conflict / revision | exactly 200 |
| Rejected | exactly 120 |
| Multi-level approval | exactly 80 |
| Event records | 6,440 |
| Ground Truth records | 6,440 |
| Authority grants | 180 |
| Final deal decisions | 800 |
| Unit-level approvals | 240 |
| Distinct deal episodes with observable missingness | exactly 80 (10%) |

Scenario-family quotas are balanced per organization: 20 routine, 10 conflict/revision, 6 rejected and 4 multi-level episodes in each of the 20 organizations. Exactly four distinct deal episodes per organization are selected for observable missingness.

## Semantics and integrity

- Real canonical organization, unit, person and role-assignment identifiers are reused; no six-person demo roster is fabricated.
- Every deal has a stable key, one ordered event chain, a closing event and exactly one final approve/reject decision.
- Conflict/revision episodes contain explicit objection and revision events.
- Multi-level episodes contain technical, finance and procurement unit approvals, each linked to a matching scoped synthetic authority grant; the final decision is separately linked to the deal-approval grant.
- Ground Truth is a separate evaluation-only projection. It preserves decision makers, outcomes, initiators, executors, authority references and source lineage.
- Actual speaker remains unknown because transcript-turn labels do not exist yet.
- Observable missingness masks only eligible fields in the observable projection. Entity/event keys, organization/deal lineage and hidden Ground Truth are preserved.
- Same seed reproduces the complete logical dataset.

## CI evidence

GitHub Actions run #45485343408 completed with **SUCCESS**. The canonical scenario report and test command both passed. The test suite checks exact quotas, all 20 organizations, staffing bounds, event lineage, missingness isolation, authority references, hidden truth separation, reproducibility and rejected configuration changes.

## Explicit boundaries

This is a **full-scale in-memory scenario dry-run**, not a persistent dataset release:
- No files were written under `src/data/generator_v4_0/`.
- No Bitrix24 activity text corpus was rendered.
- No NLP model was run.
- The generated authority grant schema is validated inside the scenario contract; a subsequent integration must invoke the existing temporal/financial/delegation authority engines rather than treat these fixture references as a substitute for those engines.
- Natural-language evidence entailment and speaker-turn attribution remain unverified.
- `generation_authorized=false` and `bulk_generation_enabled=false` remain unchanged.

## Recommended next stage — GEN-010.6

Integrate the canonical scenario events with the existing authority execution/BPMN-DMN runtime and communication renderer. Verify that the process trace, authority engine decisions, observable communications and hidden Ground Truth agree event-by-event. Only after that integration should a separate full dataset release be proposed for approval.
