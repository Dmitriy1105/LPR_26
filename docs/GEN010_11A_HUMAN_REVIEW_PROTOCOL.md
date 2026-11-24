# GEN-010.11A — Human Review Protocol

## Purpose
Blindly assess whether Generator v4.0 synthetic CRM communication texts are understandable, natural for their stated channel, and semantically supported by the visible text. This is a human-evaluation stage; generating the pack does not mean the texts passed review.

## Files and separation
- Reviewer pack: GitHub Actions artifact `gen01011a-blinded-review-pack`.
- Restricted answer key: separate artifact `gen01011a-restricted-answer-key`. Do not provide this artifact to reviewers before both independent annotations are locked.
- CI run: [Process model QC #45499384535 — SUCCESS](https://github.com/Dmitriy1105/LPR_26/actions/runs/45499384535).

The pack contains 220 records, 20 from each of 11 event classes. Deal identifiers are redacted. Event labels, source references, organization IDs, contact IDs and timestamps are excluded from reviewer records. The key maps review IDs to evaluation-only source and class labels.

## Annotation procedure
1. Assign the same blinded pack independently to Reviewer 1 and Reviewer 2.
2. Reviewers must not see the answer key, CRM metadata, source events or one another's annotations.
3. For every record, select one primary event class or `unclear`.
4. Optionally record secondary signals, but do not substitute them for the primary class.
5. Rate event clarity, naturalness and factual support on a 1–5 scale.
6. Record unsupported claims, ambiguity and comments. Judge only the visible text; do not infer facts from hidden scenario context.
7. Lock both annotation files before revealing the answer key.
8. An adjudicator resolves disagreements and records a reason. Preserve both original annotations.

## Event-class definitions
| Class | Definition |
|---|---|
| request_information | Request for initial information, documents or clarification |
| delegate | Assignment or transfer of a task to another executor |
| complete_task | Report that an assigned task has been completed |
| review | Review or discussion of materials without a standalone decision |
| recommend | Expert recommendation or proposed next action |
| object | Objection, disagreement or comment on terms |
| revise | Change or resubmission of a previously proposed version |
| unit_approval | Approval within a department's authority; not necessarily final |
| approve | Final positive decision on the deal |
| reject | Final negative decision on the deal |
| close | Recording closure of the process or deal episode |
| unclear | Text does not support a confident primary class |

## Rating scale
- 1 — very poor / unclear / unsupported
- 2 — weak; substantial ambiguity or unsupported content
- 3 — mixed; understandable but materially incomplete or awkward
- 4 — good; mostly clear and supported
- 5 — very good; clear, natural for the channel and well supported

For factual support, assess whether assertions in the communication are supported by the visible text itself. Do not treat a plausible business statement as verified merely because it sounds realistic.

## Analysis after annotation
Report:
- reviewer agreement on primary event class (raw agreement and Cohen's kappa);
- adjudicated confusion matrix against the separate answer key;
- per-class precision, recall and F1 after adjudication;
- mean/median clarity, naturalness and factual-support ratings;
- rate and categories of unsupported claims;
- disagreement examples and adjudication rationale;
- breakdown by channel.

## Acceptance
No human-review result or PASS is claimed until reviewers return completed, independent annotations and adjudication. The previous lexical benchmark's provisional quality gate remains NOT_ACCEPTED. Human review is only one component; a text-only trained baseline and a suitably de-identified real-data comparison remain separate future checks.
