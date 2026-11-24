# GEN-010.11A — Corrected Reviewer Pack and LLM Reassessment

**Date:** 2026-11-25  
**Status:** Corrected pack generated; CI PASS; human review pending  
**CI:** [Process model QC #45503163360 — SUCCESS](https://github.com/Dmitriy1105/LPR_26/actions/runs/45503163360)

## 1. Defect found in the first review pack

The original reviewer-facing communications included internal scenario metadata in the message body:
- `Контекст события: ...`
- `Область согласования: ...`

These strings exposed event-class cues and decision-scope metadata to reviewers and NLP models. The original review pack is therefore **superseded** and must not be used for final human-review acceptance.

The previous LLM annotations are retained as historical output for the contaminated pack, not treated as an independent evaluation of the corrected pack.

## 2. Renderer correction

Updated `scripts/generator_v4_communication_renderer_v1.py`:
- stopped appending observable `context_note` to the communication body;
- stopped appending decision-scope values to unit-approval communication bodies;
- set `context_note_included=false` in the structured communication metadata.

The observable source context and decision scope remain available in structured event/evaluation data; they are not rendered as text.

Updated validation:
- renderer QC now requires no internal context/scope markers in the body;
- semantic auditor treats source context as evaluator-only metadata and rejects any attempt to inject it into the rendered body;
- review-pack builder counts label leakage and fails if any marker is present.

## 3. Regression and CI

Added/updated tests:
- renderer rejects `Контекст события:`, `Область согласования:` and `unit_approval:` in communication bodies;
- semantic audit detects injected source context leakage;
- blinded pack test requires zero internal scenario label markers.

Final CI run: **SUCCESS**.  
Run URL: https://github.com/Dmitriy1105/LPR_26/actions/runs/45503163360

Artifacts:
- blinded reviewer pack v2: artifact ID `14971796778`
- restricted answer key v2: artifact ID `14972600956`

The two artifacts are separate. Do not share the answer key with any reviewer before annotation is locked.

## 4. Corrected pack properties

- 220 records.
- 11 scenario classes, 20 records per class in the sampling design.
- deterministic seed 42.
- zero visible scenario-context or decision-scope marker leakage.
- Ground Truth/source identifiers remain excluded from reviewer-facing rows.
- reviewer-facing content includes only subject, body, channel and record format.

## 5. LLM reassessment of corrected text

A separate LLM pass was performed using only the corrected reviewer-facing subject, body, channel and record format. Ground Truth, answer-key file, source event IDs and scenario metadata were not accessed.

Results:
- records assessed: 220.
- mean event clarity: 3.87 / 5.
- mean naturalness: 2.36 / 5.
- mean factual support: 3.69 / 5.
- records with at least one text-quality note: 171 / 220.
- visible internal scenario-label leakage: 0.

The LLM text-only classification was not balanced to the hidden scenario labels:
- recommend 19
- close 17
- approve 22
- review 21
- revise 28
- complete_task 16
- unclear 14
- request_information 14
- unit_approval 15
- object 20
- reject 20
- delegate 14

This is an important diagnostic: after removal of explicit scenario labels, a text-only reviewer no longer trivially recovers every class. It also shows that several generated texts remain ambiguous or overly generic.

**These are LLM judgments, not human-review results.** No inter-rater Cohen's kappa can be computed from a single LLM pass. The LLM's ratings must not be presented as human consensus.

## 6. Files

- `scripts/generator_v4_communication_renderer_v1.py`
- `scripts/generator_v4_communication_semantic_audit_v1.py`
- `scripts/test_generator_v4_communication_renderer_v1.py`
- `scripts/test_generator_v4_communication_semantic_audit_v1.py`
- `scripts/generator_v4_human_review_pack_v1.py`
- `scripts/test_generator_v4_human_review_pack_v1.py`

## 7. Next actions

1. Use the corrected reviewer pack v2 only.
2. The user is Reviewer 1; provide the corrected blank workbook.
3. Retain the LLM assessment as a separate machine annotation, not as an independent human reviewer.
4. Do not expose the restricted answer key until the user's annotation is complete and locked.
5. Obtain a genuinely independent second reviewer if inter-human Cohen's kappa is required.
6. Only after annotation is locked, reveal the key and run GEN-010.11B adjudication/evaluation.
7. GEN-010.12 comparative NLP research remains blocked until GEN-010.11A is completed.

## Decision

The label-leakage defect has been corrected and regression-tested. The corrected corpus still has weak naturalness and ambiguity signals in the LLM review. Human evaluation remains pending; NLP suitability is not accepted. Bulk generation remains disabled.
