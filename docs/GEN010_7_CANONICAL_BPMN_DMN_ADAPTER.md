# GEN-010.7 — Canonical BPMN/DMN Leaf Execution Adapter

**Status:** PASS — 800 canonical deal episodes reconciled against the registered leaf BPMN/DMN process  
**Tested commit:** `edd4a5f2ab9598b91366b2d616aa9534e5ee5c94`  
**Workflow:** [Process model QC #45487125058](https://github.com/Dmitriy1105/LPR_26/actions/runs/45487125058)  
**Branch:** `feature/generator-v4-organization-engine`

## Delivered

- `scripts/generator_v4_bpmn_canonical_adapter_v1.py` — runs canonical v4 deal decisions through the registered `deal_approval` BPMN/DMN leaf process and reconciles the output against canonical event journal, authority grants and hidden Ground Truth.
- `scripts/test_generator_v4_bpmn_canonical_adapter_v1.py` — regression tests for all-deal coverage, outcome reconciliation, authority links, closed failure behavior and generation flags.
- Updated `.github/workflows/process-model-qc.yml` to run the adapter and retain its report/test output.

## Verified results

- Canonical in-memory topology: 20 organizations, 800 deals.
- 800 BPMN/DMN leaf process executions, one per deal.
- 800/800 outcomes matched the scenario family and event journal.
- 800/800 decision actors passed the time-valid temporal authority check against the exact referenced grant.
- 800/800 deal-close records reconciled with the scenario outcome.
- Outcome distribution: 680 approve, 120 reject.
- Unauthorized decision negative test: DMN returns `deny` and BPMN terminates at `blocked`.
- Existing BPMN/DMN interpreter, process profile and complete CI workflow passed.

GitHub Actions run #45487125058 completed with **SUCCESS**.

## Scope limitation — do not overstate this as full process orchestration

The adapter executes the registered `deal_approval` leaf process only. It does not yet execute the full corporate composite process, including BPMN `callActivity` orchestration for technical expertise, budget escalation and multi-level approvals. The restricted `process_executor_v4.py` does not implement those callActivity semantics.

The scenario journal and authority layer independently establish the 240 unit-approval decisions; this stage does not claim those approvals were replayed through a composite BPMN call chain. Nor does it validate rendered natural-language communication entailment.

## Generation boundary

All data remains in-memory QC only. No persistent v4 dataset, Bitrix24 activity corpus or NLP corpus was generated. `generation_authorized=false` and `bulk_generation_enabled=false` remain unchanged.

## Next stage — GEN-010.8

Implement canonical composite BPMN orchestration with explicit callActivity semantics for technical, budget, unit and final-decision subprocesses. Reconcile each process task and subprocess result against the ordered event journal and time-valid authority. Then implement the canonical communication renderer and validate source text/participants against event Ground Truth. Full dataset generation remains a separately gated decision.
