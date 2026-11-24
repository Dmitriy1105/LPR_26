# GEN-010.4 — Scenario Event Attribution Integration

**Status:** PASS — bounded integration QC  
**Tested commit:** `82847ba7e79d75715bc986e6fe9ec031541cf303`  
**Workflow:** [Process model QC #45484198196](https://github.com/Dmitriy1105/LPR_26/actions/runs/45484198196)  
**Branch:** `feature/generator-v4-organization-engine`

## Delivered

- `scripts/generator_v4_decision_attribution_v1.mjs` — event-level attribution projection joining Scenario Engine events, Bitrix24-style communications and hidden Ground Truth.
- `scripts/test_generator_v4_decision_attribution_v1.mjs` — deterministic positive and mutation-based negative tests.
- Updated `.github/workflows/process-model-qc.yml` to run the new Node.js test and retain its JSON report artifact.

## Attribution contract

Each event-level record keeps these dimensions separate:
- participants;
- utterance/document author;
- actual speaker (unknown until transcript-turn annotation exists);
- action executor (only for `complete_task` and `revise` events);
- target and addressees;
- formal decision maker and outcome (only for `approve` / `reject`);
- authority grant references;
- confirming source and SHA-256 digest of the source communication.

Unknown speaker attribution is preserved as `null` with `unknown_no_turn_annotation`; the implementation does not equate email/document author with actual speaker. Source evidence offsets remain explicitly `not_annotated`, not fabricated.

## QC performed

- Deterministic in-memory sample: 5 organizations × 6 deals = 30 deal episodes, seed 42.
- One attribution record required for each source event.
- Cross-check of participant list, author, executor semantics, decision maker, authority evidence, source reference, event time and source-text digest.
- Nine negative mutations: incorrect participants, author, unsupported speaker, executor, authority refs, confirming source, evidence digest, missing record and wrong organization.
- Existing attribution-chain regression also remains in the CI job.

GitHub Actions run #45484198196 completed with **SUCCESS**.

## Important limitations — not a full v4.0 data release

This stage proves a structured attribution projection over the current Scenario Engine fixture; it does not yet prove natural-language entailment, speaker identification from transcript turns, or BPMN trace equivalence.

The inspected `scenario_engine_v4.mjs` remains a legacy/demo profile with a fixed six-person role list, 5 organizations × 6 deals in the current integration harness, and a 40/40/20 scenario split. It does not yet satisfy the approved v4.0 target of 20 organizations, variable 30–40 employee rosters, 800 deals and exact 50/25/15/10 family counts. Do not describe this 30-deal QC fixture as the v4.0 production dataset.

## Generation boundary

Only in-memory QC data was produced. No persistent dataset, 800 deals, CRM fixtures or bulk communication corpus was generated. Generation authorization flags remain false.

## Recommended next work

GEN-010.5 — replace the current fixed-role scenario fixture with a canonical v4 scenario adapter that consumes the 20 Organization Engine outputs, preserves exact scenario-family quotas, binds each action to time-valid authority, and emits event-level Ground Truth. First validate on a small in-memory subset; only after that run a full-scale dry-run QC, not bulk generation.
