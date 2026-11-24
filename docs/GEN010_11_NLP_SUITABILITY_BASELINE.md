# GEN-010.11 — NLP Suitability Baseline Evaluation

**Status:** Benchmark pipeline CI PASS; NLP quality gate NOT ACCEPTED  
**Branch:** `feature/generator-v4-organization-engine`  
**CI run:** [Process model QC #45498158373 — SUCCESS](https://github.com/Dmitriy1105/LPR_26/actions/runs/45498158373)

## Objective

Evaluate whether rendered Generator v4 communications are useful as NLP inputs, rather than merely structurally valid synthetic records.

The benchmark predictor receives only `body` text. The evaluator joins `event_type` labels and source identifiers only after prediction. The split is grouped by organization: ORG-0001..ORG-0016 development, ORG-0017..ORG-0020 held out.

## Dataset

- 20 organizations
- 800 deal episodes
- 6,440 observable events
- 6,440 rendered communications
- 6,440 unique source-event links
- All 11 event classes represented

## Baseline results

The current predictor is an interpretable lexical rules baseline, not a trained ML/NLP model.

| Metric | Result |
|---|---:|
| Overall event-type accuracy | **51.86%** |
| Macro F1 | **54.31%** |
| Development organization accuracy | 51.79% |
| Held-out organization accuracy | 52.17% |

### Binary event tasks

| Task | Precision | Recall | F1 |
|---|---:|---:|---:|
| Objection detection | 0.598 | 0.930 | 0.728 |
| Revision detection | 0.189 | 0.610 | 0.289 |
| Recommendation detection | 1.000 | 0.363 | 0.532 |
| Final decision detection | 0.787 | 0.861 | 0.823 |

### Interpretation

- The baseline identifies some high-signal classes, especially rejection (F1 0.929), objection (F1 0.728) and final decisions (F1 0.823).
- It confuses complete_task with delegate and revision; complete_task F1 is only 0.140.
- Request-information recall is low (0.174).
- Unit approval is confused with other approval/review events (F1 0.541).
- Similar accuracy on held-out organizations does not prove generalization to real CRM messages: all organizations use the same synthetic rendering system and phrase inventory.

## Attribution and chronology

**Person identity from body text: SAFE_ABSTENTION.**

- Predicted person IDs: 0
- Abstained records: 6,440
- Verified person-identity claims: 0

This is the correct outcome. The renderer does not have turn-level speaker annotations, and the author/actor fields in the communication envelope are structured CRM metadata, not evidence extracted from the text. Do not train a speaker-attribution model against the document author field as though those concepts were interchangeable.

Chronology is currently carried by structured timestamps and source-event links. It has not yet been reconstructed from free text.

## Quality gate

The provisional engineering thresholds are:
- event-type accuracy >= 0.80
- event-type macro F1 >= 0.70

Measured results (0.5186 / 0.5431) are below both. Therefore the **NLP quality gate is NOT_ACCEPTED**, even though the benchmark code and regression tests execute successfully in CI.

These are provisional thresholds and must be confirmed or revised after the human-review protocol is completed. CI PASS means the benchmark ran without implementation errors; it does not mean the data passed NLP suitability.

## Human evaluation — not yet performed

A blinded review protocol is required before the synthetic texts can be considered human-validated.

Proposed sample: 220 communications, stratified as 20 records per event type, selected deterministically across channel and organization where possible. The reviewer must not see the Ground Truth event label while annotating.

For each sample, reviewers assess:
1. Does the text clearly express one primary event?
2. Is the event class identifiable without CRM metadata?
3. Is the text factually supported by the visible source context?
4. Does it introduce unsupported facts, roles, decisions, deadlines or outcomes?
5. Is the distinction between recommendation, unit approval and final decision clear?
6. Is the communication natural enough for the claimed channel (email, call summary, meeting record)?
7. Is the text ambiguous or contradictory?

Two reviewers should annotate independently; disagreements should be adjudicated. Record agreement and class-specific confusion, not only a single overall score. Human review is pending; no human-review PASS is claimed.

## Next work

1. Generate the deterministic blinded 220-record review pack and a separate evaluator-only answer key.
2. Conduct independent human annotation and adjudication.
3. Improve renderer semantics specifically for complete_task/delegate/revise, request_information and unit_approval.
4. Add paraphrase and counterfactual tests to ensure class predictions do not depend on one fixed phrase.
5. Train/evaluate a genuine text-only baseline (e.g. TF-IDF + linear classifier) with group-aware organization splits, keeping all preprocessing inside the training folds.
6. Evaluate multi-label business signals separately from event-type classification.
7. Keep person-level attribution out of model claims until real turn-level speaker evidence is available.
8. Compare with a consented, de-identified real CRM evaluation set before making claims about production transfer.

## Decision

Do not authorize bulk fixture generation for NLP training yet. Generator v4 has a structurally audited scenario and communication layer, but this first text-only benchmark shows that event semantics are not yet reliably distinguishable across all classes. Continue with blinded human evaluation and targeted renderer revision.
