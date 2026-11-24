# LPR_26 — GEN-010.11 Checkpoint (2026-11-25)

## Repository
- `Dmitriy1105/LPR_26`
- Branch: `feature/generator-v4-organization-engine`
- Latest benchmark CI: [Process model QC #45498158373 — SUCCESS](https://github.com/Dmitriy1105/LPR_26/actions/runs/45498158373)

## Prior state
GEN-010.10 semantic/attribution audit passed over all 6,440 rendered communications. Full checkpoint:
`docs/checkpoints/2026-11-25_LPR_26_GEN010_10_checkpoint.md`

## GEN-010.11 started
Added:
- `scripts/generator_v4_nlp_suitability_benchmark_v1.py`
- `scripts/test_generator_v4_nlp_suitability_benchmark_v1.py`
- CI benchmark/report and regression-test steps in `.github/workflows/process-model-qc.yml`

Benchmark design:
- Predictor input: rendered body text only.
- Evaluation labels joined only after prediction.
- Organization-group holdout: ORG-0001..0016 development; ORG-0017..0020 held out.
- Deterministic interpretable lexical baseline; explicitly not a trained model.

## Measured baseline (6,440 records)
- Event type accuracy: 0.5186.
- Macro F1: 0.5431.
- Development accuracy: 0.5179.
- Held-out accuracy: 0.5217.
- Objection F1: 0.7280.
- Revision F1: 0.2888.
- Recommendation F1: 0.5321.
- Final-decision F1: 0.8227.
- Person attribution from text: safe abstention on 6,440 / 6,440; zero guessed IDs.
- Benchmark implementation CI: SUCCESS.
- NLP quality gate: NOT_ACCEPTED (provisional thresholds accuracy >= 0.80 and macro F1 >= 0.70).

Interpretation: good structural QA does not imply strong text-only NLP utility. Complete-task/delegation/revision and request-information classes are difficult to separate. The lexical baseline is a diagnostic smoke test, not a learned NLP model. Similar held-out accuracy does not prove transfer to real CRM communications because organizations share the same synthetic templates.

## Human evaluation
Not performed yet. Proposed blinded sample: 220 records, 20 per event type, deterministic and stratified across channels/organizations where possible. Two independent reviewers; adjudicate disagreements. Review naturalness, event identifiability, context entailment, unsupported facts, decision hierarchy and channel suitability. Keep answer key separate from blinded sample.

## Next steps
1. Generate blinded 220-record sample and separate answer key.
2. Perform independent human review and adjudication.
3. Improve renderer for complete_task/delegate/revise, request_information and unit_approval.
4. Add counterfactual and paraphrase robustness tests.
5. Add a real trained text-only baseline (TF-IDF + linear model) with group-aware splits and train-fold-only preprocessing.
6. Keep person attribution unclaimed until turn-level speaker evidence exists.
7. Compare against a consented, de-identified real CRM benchmark before production claims.

## Safety gates
- Do not enable bulk generation or persistent fixture writes.
- Do not train person-level attribution using author/participant metadata as proxy speaker labels.
- Do not describe the current lexical baseline as an ML model.
- Do not claim NLP suitability PASS until the quality gate and blinded human evaluation are accepted.
