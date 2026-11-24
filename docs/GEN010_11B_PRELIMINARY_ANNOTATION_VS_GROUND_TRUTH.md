# GEN-010.11B — Preliminary Annotation vs Ground Truth

**Status:** preliminary automated baseline completed; not LLM validation and not human expert validation.

## Important provenance correction
The corrected-v2 annotation files previously described in chat as LLM-generated were in fact produced by a deterministic Python keyword/rule-assisted pass. This was a provenance error in the earlier description. The frozen labels were generated before the restricted answer key was opened, so they can be compared with Ground Truth as a blind automated baseline. They must not be presented as a true LLM inference or human expert assessment.

## Sample and method
- 220 records, balanced: 20 examples for each of 11 synthetic Ground Truth event classes.
- Join key: `review_id`.
- Predicted label: `reviewer_llm_v2.primary_event_type`.
- Reference label: `ground_truth_event_type` from the restricted corrected-v2 answer key.
- `unclear` predictions count as errors against the 11 Ground Truth classes.
- Cohen's kappa is not applicable: only one annotation stream exists.

## Results
- Accuracy: 0.8636 (190/220)
- Macro Precision across 11 Ground Truth classes: 0.9448
- Macro Recall across 11 Ground Truth classes: 0.8636
- Macro F1 across 11 Ground Truth classes: 0.8906
- Macro F1 with an explicit 12th `unclear` category: 0.8164

### Per-class results
| Class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| approve | 20 | 0.9091 | 1.0000 | 0.9524 |
| close | 20 | 1.0000 | 0.8500 | 0.9189 |
| complete_task | 20 | 0.9375 | 0.7500 | 0.8333 |
| delegate | 20 | 1.0000 | 0.7000 | 0.8235 |
| object | 20 | 1.0000 | 1.0000 | 1.0000 |
| recommend | 20 | 1.0000 | 0.9500 | 0.9744 |
| reject | 20 | 1.0000 | 1.0000 | 1.0000 |
| request_information | 20 | 1.0000 | 0.7000 | 0.8235 |
| review | 20 | 0.7619 | 0.8000 | 0.7805 |
| revise | 20 | 0.7143 | 1.0000 | 0.8333 |
| unit_approval | 20 | 1.0000 | 0.7500 | 0.8571 |

### By channel
- call: 35/40 = 0.8750
- email: 67/80 = 0.8375
- meeting: 88/100 = 0.8800

## Interpretation
The automated baseline separates several explicitly worded classes well. Its weaker areas are `review`, `revise`, `delegate`, `request_information`, `complete_task`, and `unit_approval`. This result is not evidence that the generator itself has 86.36% quality: it measures label recovery from this deliberately balanced sample.

The previous text ratings (clarity, naturalness, factual support) are subjective scripted scores and must not be described as LLM judgments. The sample also contains repeated generic boilerplate; that remains a generator quality issue independent of label accuracy.

## Next valid experiment
Run a true LLM semantic annotation on a new, blinded sample. Freeze its output and provenance before opening the matching answer key. Then compare it to Ground Truth separately from this keyword/rule baseline. Human review can be added later when available.
