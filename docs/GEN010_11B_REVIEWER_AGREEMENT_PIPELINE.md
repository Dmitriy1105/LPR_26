# GEN-010.11B — Reviewer Agreement and Adjudication Pipeline

**Implementation status:** READY; waiting for two independent human annotation files  
**CI:** [Process model QC #45500713102 — SUCCESS](https://github.com/Dmitriy1105/LPR_26/actions/runs/45500713102)

## Added components

- `scripts/generator_v4_human_review_evaluator_v1.py`
- `scripts/test_generator_v4_human_review_evaluator_v1.py`

The evaluator accepts four separate JSON inputs:
1. Reviewer 1 annotations
2. Reviewer 2 annotations
3. Adjudicated annotations with reasons
4. Restricted answer key (must remain hidden until both reviewer files are locked)

## Metrics

- Raw inter-rater agreement.
- Cohen's kappa, reported with expected chance agreement and class categories.
- Agreement broken down by communication channel.
- Disagreement register with adjudication decisions and reasons.
- Adjudicated classification accuracy, per-class precision/recall/F1 and confusion matrix against the synthetic Ground Truth.
- Reviewer ratings (clarity, naturalness, factual support): count, mean, median and distribution.
- Rate and count of records with unsupported-claim annotations.

## Validation rules

- Exactly 220 unique review IDs must be present in each file.
- Every primary label must be one of the 11 event classes or `unclear`.
- Ratings must be integers from 1 to 5 or null.
- Missing/duplicate IDs and invalid labels fail closed.
- No metric is emitted from incomplete annotation files.

## Important statistical interpretation

The sample contains 20 records per Ground Truth class by design. It is a balanced diagnostic sample, not a prevalence-representative sample of the full generated corpus. Report class-wise metrics and raw counts; do not interpret sample accuracy as an estimate of production-population accuracy without weighting to the corpus class distribution.

Cohen's kappa is prevalence-sensitive, so it must be reported together with raw agreement and label distributions. A high reviewer agreement does not prove the texts are realistic; it only measures consistency between annotators.

Agreement with Ground Truth evaluates consistency with the synthetic scenario contract, not truth about actual customer behavior. Human factual-support ratings assess only claims visible in each text, not hidden scenario metadata.

## CI verification

- Overall Process model QC: SUCCESS.
- Blinded review pack build: SUCCESS.
- Review pack regression tests: SUCCESS.
- Evaluator regression tests: SUCCESS.
- No human annotations have been fabricated or filled in.
- No human-review PASS is claimed.

## Required external input to complete GEN-010.11A

Two reviewers must independently annotate all 220 records and lock their files before the answer key is opened. An adjudicator must resolve disagreements and complete the adjudication file. Only then run:

```bash
python scripts/generator_v4_human_review_evaluator_v1.py \
  --reviewer1 reviewer-1.json \
  --reviewer2 reviewer-2.json \
  --adjudicated adjudicated.json \
  --answer-key human-review-answer-key.json \
  --output gen01011b-human-evaluation-report.json
```

Do not start comparative NLP research (GEN-010.12) until this human-review step has actual annotations and a documented result.
