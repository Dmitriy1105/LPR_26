# GEN-010.10 — Semantic and Attribution Audit of Rendered Communications

**Status:** AUTOMATED QC PASS  
**Branch:** `feature/generator-v4-organization-engine`  
**CI:** [Process model QC #45496578780 — SUCCESS](https://github.com/Dmitriy1105/LPR_26/actions/runs/45496578780)

## Scope

Independent audit of 6,440 communications produced by GEN-010.9. The renderer receives only observable event projections and organization metadata. Ground Truth is supplied only to the post-render auditor as an evaluation oracle; it is never passed to the renderer.

## Implemented

- `scripts/generator_v4_communication_semantic_audit_v1.py` — independent audit of event semantics, author, executor, decision actor, addressee, participant list, role labels, channel format, context fidelity, missingness, source chronology and authority references.
- `scripts/test_generator_v4_communication_semantic_audit_v1.py` — seven tests, including deliberate corruptions of author, channel, role, context, closure outcome and unit-approval meaning.
- `scripts/generator_v4_communication_renderer_v1.py` — explicit `record_format`, `action_executor_contact_id`, `decision_actor_contact_id` and `confirming_source_ref` fields derived exclusively from observable event attributes.
- `.github/workflows/process-model-qc.yml` — semantic audit and regression tests run in CI.

## Verified results

| Audit | Records/checks | Result |
|---|---:|---|
| Communication coverage | 6,440 | PASS |
| Author/document provenance | 6,440 | PASS |
| Addressee and participants | 6,440 | PASS |
| Role-label reconciliation | 6,440 | PASS |
| Confirming source and chronology | 6,440 | PASS |
| Channel and record format | 6,440 | PASS |
| Semantic event alignment | 6,440 | PASS |
| Executor reconciliation | 1,000 | PASS |
| Decision actor and authority reconciliation | 1,040 | PASS |
| Missingness and speaker uncertainty | 6,440 | PASS |

Additional observations:
- 5,772 records contain visible source context.
- 668 records have masked or absent context.
- Unique source coverage: 6,440 / 6,440.
- Audit errors: 0.
- Regression tests: 7 / 7 passed.
- Renderer remains deterministic and in-memory; no persistent CRM fixtures were written.

## Attribution contract

The communication record now explicitly carries:
- `author_contact_id`: author of the communication/document, derived from observable event actor.
- `action_executor_contact_id`: populated only for `complete_task` and `revise`.
- `decision_actor_contact_id`: populated only for `approve`, `reject` and `unit_approval`.
- `addressee_contact_ids`: derived from observable target, or empty when target is unavailable.
- `participant_contact_ids`: author and observable addressee.
- `confirming_source_ref`: exact source reference of the originating event.
- `speaker_contact_id`: remains null until turn-level annotations exist.

The auditor independently reconciles executor and decision actor fields against evaluation-only Ground Truth and validates decision actor authority grant references. Ground Truth does not influence text generation.

## Important interpretation

**PASS means automated structural and rule-based semantic checks passed. It does not mean a human has certified the naturalness of every text.** The current generator is deterministic and template/composition based, not an LLM trained on real CRM conversations. Rule checks cannot fully establish naturalness, factual entailment or downstream NLP utility.

Calls are summaries, not verbatim transcripts. Speaker-turn identity remains unknown. Bulk generation and persistent fixture writes remain disabled.

## Next stage — GEN-010.11

Run independent quality evaluation focused on NLP suitability:
1. Human review of a stratified sample from every event type and communication channel.
2. Evaluate factual entailment: every sentence must be supported by the observable event and visible context.
3. Evaluate role confusion and decision leakage using adversarial negative cases.
4. Test downstream NLP tasks: event classification, objection/revision detection, decision-language classification, attribution extraction and chronology reconstruction.
5. Compare metrics with the earlier v3.2.x corpus without claiming equivalence to real customer communications.
6. Set explicit acceptance thresholds before any production-sized fixture generation is authorized.

Financial authority bands and monetary evidence remain a separate open contract gap and must be resolved before financial decision scenarios can be treated as validated.
