# LPR_26 — GEN-010.11B Checkpoint (2026-11-25)

## Repository
- Repository: `Dmitriy1105/LPR_26`
- Branch: `feature/generator-v4-organization-engine`
- Current phase: GEN-010.11B preliminary automated annotation vs synthetic Ground Truth.

## Provenance correction — important
The corrected-v2 annotation files previously described in chat as LLM-generated were produced by a deterministic Python keyword/rule-assisted pass, not a true LLM inference call and not a human expert. This provenance error is corrected in `docs/GEN010_11A_HUMAN_REVIEW_PROTOCOL.md` and the GEN-010.11B report. The frozen annotation was generated before opening the restricted answer key and remains usable as a blinded automated baseline.

## Sample and Ground Truth
- 220 corrected-v2 communications, 20 per each of 11 Ground Truth classes.
- Blinded pack from CI run #45503163360.
- Restricted answer key artifact ID: 14972600956.
- Reviewer-facing pack artifact ID: 14971796778.
- Ground Truth opened only after the annotation file was frozen.

## Preliminary results
- Accuracy: 0.8636 (190/220)
- Macro Precision (11 Ground Truth classes): 0.9384
- Macro Recall (11 Ground Truth classes): 0.8636
- Macro F1 (11 Ground Truth classes): 0.8906
- Macro F1 with explicit 12th `unclear` prediction class: 0.8164
- Channel accuracy: call 0.8750 (35/40); email 0.8375 (67/80); meeting 0.8800 (88/100).

## Main weaker classes
- review: F1 0.7805
- revise: F1 0.8333
- complete_task: F1 0.8333
- delegate: F1 0.8235
- request_information: F1 0.8235
- unit_approval: F1 0.8571

## Interpretation
This is a rule-assisted automated classification baseline, not an LLM benchmark or expert validation. It measures recovery of synthetic event labels from a deliberately balanced diagnostic sample. It does not prove real-world realism or full-corpus prevalence performance. No Cohen's kappa is calculated because there is only one annotation stream.

## CI verification
- [Process model QC #45505491176 — SUCCESS](https://github.com/Dmitriy1105/LPR_26/actions/runs/45505491176)
- New evaluator regression tests: 4/4 PASS.

## Added implementation
- `scripts/generator_v4_annotation_ground_truth_audit_v1.py`
- `scripts/test_generator_v4_annotation_ground_truth_audit_v1.py`
- `docs/GEN010_11B_PRELIMINARY_ANNOTATION_VS_GROUND_TRUTH.md`

## Next step
1. Complete a true LLM semantic annotation as a separate, explicitly recorded blinded pass on a fresh sample; freeze it before opening the corresponding answer key.
2. Compare the true LLM pass with Ground Truth separately from the rule-assisted baseline.
3. Human expert review remains pending and must not be simulated.
4. GEN-010.12 comparative trained NLP research should use clear split-by-organization design and remain separate from this rule-based baseline.
