# LPR_26 — Checkpoint: Generator v4.0 / GEN-003

**Checkpoint date:** 2026-11-24  
**Working repository:** `Dmitriy1105/LPR_26`  
**Working branch:** `feature/generator-v4-organization-engine`  
**Checkpoint commit:** `57a9702d4216b934d364d8e50ea75af35cf9a040`  
**Verified CI:** Process Model QC #169 — SUCCESS, exact same commit SHA  
**CI run:** https://github.com/Dmitriy1105/LPR_26/actions/runs/45454548022

This checkpoint is the resume baseline for the next work session. It records committed source and the downloaded CI artifact, not assumptions about unexecuted features.

## 1. Project architecture and agreed boundaries

- The project generates **synthetic corporate/CRM data**. There is no live Bitrix24 portal required for this work.
- Generator v4.0 is responsible for generating internally consistent organizations, roles, authority, business scenarios, BPMN/DMN-derived events, CRM activities/communications and a separately stored Ground Truth layer.
- NLP is a **separate downstream analysis pipeline**. Do not embed NLP inference, classification or quality scoring into the generator.
- Communication text must be derived from the underlying synthetic scenario events. Do not generate unrelated free-standing CRM texts.
- Preserve explicit attribution distinctions: participant, author/speaker, target/addressee, decision-maker/approver, executor and confirming evidence/source must not be conflated.
- Existing code should be inspected before editing. Avoid repeating completed work or broad rewrites; fix demonstrated defects and test them.

## 2. Current implementation state

### GEN-001 — Authority Enforcement
- Dedicated authority regression was added in `scripts/test_scenario_authority_enforcement_v1.mjs`.
- Baseline valid scenario plus five invalid cases: unauthorized actor, expired grant, future grant, wrong scope and wrong organization.
- Earlier CI #160 was reported SUCCESS; see the previous conversation record if exact run metadata is needed.
- Status in audit: CLOSED for tested baseline.

### GEN-002 — Scenario-to-BPMN/DMN integration
- Bridge: `scripts/generator_v4_bpmn_integration_v1.py`.
- Runs synthetic deals through `corporate_multilevel_universal`.
- Baseline: seed 42, 5 organizations, 30 deals, 30 BPMN/DMN executions, 30 matching outcomes, deterministic replay.
- Uses explicit demo-profile actor mapping (P1/P2/P3/P4); dynamic mapping for arbitrary generated organizations remains a limitation.
- Status in audit: CLOSED for baseline scope, not full arbitrary-organization coverage.

### GEN-003 — Scenario-Based CRM Communication Generator
Committed implementation:
- `scripts/scenario_communication_generator_v1.mjs`
- `scripts/test_scenario_communication_generator_v1.mjs`
- `scripts/scenario_engine_v4.mjs` remains the synthetic world/event source.
- `.github/workflows/process-model-qc.yml` runs the communication regression and uploads `scenario-communication-generator-qc.json`.
- `scripts/generator_v4_architecture_audit_v1.py` reads the communication QC report and determines GEN-003 status from its evidence.
- `scripts/test_generator_v4_architecture_audit_v1.py` asserts the GEN-003 baseline.
- `docs/GENERATOR_V4_ARCHITECTURE_AUDIT.md` records GEN-003 as CLOSED (baseline scope).

Verified artifact from CI #169:
- seed: 42
- organizations: 5
- deals: 30
- source events: 252
- rendered CRM-style communications: 252
- linked source events: 252
- channels: email 104, call 44, meeting 104
- validation: PASS, zero errors
- deterministic replay: true

Each generated communication currently contains Bitrix-style activity fields including ID, TYPE_ID, CHANNEL, SUBJECT, DESCRIPTION, CREATED, AUTHOR_ID, RESPONSIBLE_ID, OWNER_TYPE_ID, OWNER_ID, COMMUNICATIONS, SOURCE_EVENT_ID, DEAL_ID, ORGANIZATION_ID, EVENT_TYPE and PREVIOUS_EVENT_ID.

**Important quality limitation:** this is an initial deterministic template-based projection: one CRM-style communication per source event. It proves traceability and contract mechanics, but does NOT yet prove realistic, diverse, multi-turn corporate dialogue. Do not overstate its linguistic realism. Improve that only after the structural contract and Ground Truth are defined.

## 3. CI history at checkpoint

- CI #167: FAILURE — stale audit test still expected GEN-002 to be OPEN after it had been closed.
- CI #168: SUCCESS — intermediate corrected audit-test commit.
- CI #169: SUCCESS — final checkpoint commit `57a9702d4216b934d364d8e50ea75af35cf9a040`.
- CI #169 completed all 75 workflow steps. The downloaded `process-qc` artifact contained `scenario-communication-generator-qc.json` with PASS and the counts listed above.
- Exact CI #169 URL: https://github.com/Dmitriy1105/LPR_26/actions/runs/45454548022

## 4. Current audit register

See `docs/GENERATOR_V4_ARCHITECTURE_AUDIT.md`.

- GEN-001: CLOSED (tested authority baseline).
- GEN-002: CLOSED (seed-42 integration baseline; explicit demo actor mapping remains limited).
- GEN-003: CLOSED (initial event-to-communication projection baseline; text diversity/realism not accepted as complete).
- GEN-004: OPEN — scenario-linked Ground Truth and event attribution.
- GEN-005: OPEN — fixture count discrepancy: committed legacy manifest totals 677 (1 company + 30 contacts + 18 deals + 44 invoices + 540 activities + 44 tasks), while prior v4 contract baseline is 767. Do not silently add 90 records or change target; reconcile version/contract first.
- GEN-006: OPEN — `docs/GENERATOR_V4_DATA_CONTRACT.md` is `PROPOSAL_REVIEW_REQUIRED`, not approved.
- GEN-007: OPEN — prior architecture defect registry still contains PARTIAL items.
- GEN-008 / GEN-009: DECISION_REQUIRED — restricted custom BPMN/DMN profile versus executable-standard BPMN model expectations. Do not claim general BPMN 2.0 / DMN 1.3 conformance.

## 5. Next work: GEN-004

**GEN-004: Ground Truth & Event Attribution Model**

Implement a separate, machine-readable Ground Truth output derived from the hidden scenario state, not inferred from generated communication text. It should be linked to:
- scenario/process instance;
- source business event and event chronology;
- deal and organization;
- person IDs;
- participant versus author/speaker;
- addressee/target;
- action executor;
- authority holder / actual decision-maker;
- decision outcome and approval/rejection;
- confirming source/evidence references;
- provenance and confidence/status where a fact is not independently established.

Requirements:
1. Keep Ground Truth separate from CRM communication records and separate from NLP outputs.
2. Preserve exact source-event links and immutable IDs.
3. Do not assume every event has a distinct author, target, executor or approver; represent not-applicable/unknown explicitly.
4. Test positive and negative cases, missing/ambiguous attribution, referential integrity, chronology, uniqueness and deterministic replay.
5. Do not leak Ground Truth labels into communication text or model-facing NLP inputs. Provide a clear split between generated observations and hidden gold labels.
6. Define schema and acceptance criteria before claiming GEN-004 complete.

After GEN-004, reconcile GEN-005/GEN-006 and build a full generator dataset export only against an approved data contract. Then address remaining architecture limits and perform a full data-quality/realism audit.

## 6. Resume instructions

At the next session:
1. Open this checkpoint first.
2. Verify the branch head and latest CI in GitHub; do not assume the branch is unchanged.
3. Inspect current files and the architecture audit before editing.
4. Continue with GEN-004 only; do not redo GEN-001–GEN-003 baseline work.
5. Keep NLP separate from the generator.
6. Run focused tests, then Process Model QC; inspect the exact failing log if any test fails. Do not claim success until the exact latest commit has a passing run.

## 7. Resume prompt

> Продолжаем проект LPR_26. Открой checkpoint `docs/checkpoints/2026-11-24_LPR_26_Generator_v4_GEN003_checkpoint.md` в репозитории `Dmitriy1105/LPR_26`, ветка `feature/generator-v4-organization-engine`. Сначала проверь актуальный HEAD и GitHub Actions. Не повторяй GEN-001–GEN-003. Продолжи с GEN-004: спроектируй и реализуй отдельный Ground Truth & Event Attribution Model, связанный с исходными синтетическими BPMN-событиями. Ground Truth не смешивать с CRM-текстами и NLP; NLP остаётся отдельным downstream-контуром. Перед изменениями проверь существующие файлы и Data Contract, затем добавь тесты и запусти QC.
