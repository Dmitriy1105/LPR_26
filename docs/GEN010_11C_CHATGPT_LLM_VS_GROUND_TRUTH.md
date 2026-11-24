# GEN-010.11C — ChatGPT LLM vs Ground Truth

**Status:** COMPLETED  
**Sample:** GEN01011B1-SEED-20261125  
**Records:** 220 (20 per intended event class)

## Annotation provenance and lock

- Annotator: ChatGPT GPT-6.2, semantic annotation in the current conversation.
- No external provider API was called.
- Ground Truth was not accessed during annotation.
- Annotation was locked before the restricted answer key was opened.
- Blind pack SHA-256: `86e95f4219ad87ed2e92416e53b0d9ab1374c75a78159aa780e38489c2251f61`.
- Annotation SHA-256: `8870dd8aacd52687a5718d659357418386f9a0849e5ea8a8bbbdcb090eac5d2e`.
- Both hashes match the annotation manifest.

## Overall metrics

| Metric | Result |
|---|---:|
| Correct | 213 / 220 |
| Incorrect | 7 / 220 |
| Accuracy | 96.82% |
| Macro Precision | 96.80% |
| Macro Recall | 96.80% |
| Macro F1 | 96.80% |
| Weighted F1 | 96.80% |

## Per-class metrics

| Class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| approve | 20 | 0.9091 | 1.0000 | 0.9524 |
| close | 20 | 1.0000 | 1.0000 | 1.0000 |
| complete_task | 20 | 0.9091 | 1.0000 | 0.9524 |
| delegate | 20 | 0.8500 | 0.8500 | 0.8500 |
| object | 20 | 1.0000 | 1.0000 | 1.0000 |
| recommend | 20 | 1.0000 | 1.0000 | 1.0000 |
| reject | 20 | 1.0000 | 1.0000 | 1.0000 |
| request_information | 20 | 1.0000 | 0.8500 | 0.9189 |
| review | 20 | 1.0000 | 0.9500 | 0.9744 |
| revise | 20 | 1.0000 | 1.0000 | 1.0000 |
| unit_approval | 20 | 1.0000 | 1.0000 | 1.0000 |

## Accuracy by channel

| Channel | N | Accuracy |
|---|---:|---:|
| meeting | 100 | 99.00% |
| email | 80 | 92.50% |
| call | 40 | 100.00% |

Channel is reported only as a post-hoc slice from the restricted key; it was not provided to the annotator.

## LLM text-quality ratings

| Criterion | Mean |
|---|---:|
| Self-reported confidence | 0.937 |
| Event clarity | 4.836 / 5 |
| Naturalness | 2.514 / 5 |
| Factual support | 5.000 / 5 |

The confidence is self-reported and not calibrated. The naturalness score is materially lower than classification performance and requires separate renderer improvement.

## Misclassifications

Seven records were misclassified:

- HR-031, HR-052, HR-068: request_information → delegate (3)
- HR-084: review → approve (1)
- HR-172: delegate → approve (1)
- HR-185, HR-191: delegate → complete_task (2)

The recurring issue is confusion between requesting information, assigning a task, and recording task completion. These distinctions should be made explicit in event semantics and rendered text.

## Interpretation and limitations

1. This is a synthetic, balanced benchmark: 20 records per each of 11 intended classes.
2. Agreement measures recovery of generator-assigned labels, not real-world CRM validity or semantic completeness.
3. Annotation was performed by ChatGPT GPT-6.2 in-conversation; no external batch API inference was called.
4. This is one model annotation pass, not independent multi-rater human validation.
5. High event-class accuracy does not imply realistic communication. Mean naturalness of 2.51/5 is a separate quality concern.
6. No Cohen's kappa is reported because there are not two independent raters.

## Decision

GEN-010.11C comparison is complete. Do not treat 96.82% accuracy as a global generator quality score. Prioritize Renderer improvements for naturalness and semantic separation of request_information, delegate, and complete_task, then repeat on a new blind holdout.
