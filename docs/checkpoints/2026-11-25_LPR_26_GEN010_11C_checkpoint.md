# LPR_26 checkpoint — GEN-010.11C

**Date:** 2026-11-25  
**Repository:** Dmitriy1105/LPR_26  
**Branch:** feature/generator-v4-organization-engine

## Completed

- Verified locked annotation file has 220 unique IDs matching the blinded pack and restricted answer key.
- Verified annotation SHA-256: `8870dd8aacd52687a5718d659357418386f9a0849e5ea8a8bbbdcb090eac5d2e`.
- Verified blind pack SHA-256: `86e95f4219ad87ed2e92416e53b0d9ab1374c75a78159aa780e38489c2251f61`.
- Confirmed both hashes match the annotation manifest before opening the restricted answer key.
- Opened the separate restricted answer key only after the annotation lock.
- Compared all 220 predictions against Ground Truth.

## Results

- Accuracy: 96.82% (213/220)
- Macro Precision: 96.80%
- Macro Recall: 96.80%
- Macro F1: 96.80%
- Weighted F1: 96.80%
- Misclassifications: 7
- Mean naturalness: 2.514/5
- Mean event clarity: 4.836/5
- Mean factual support: 5.000/5
- Mean self-reported confidence: 0.937 (not calibrated)

## Main error pattern

Confusions between `request_information`, `delegate`, and `complete_task`; plus one `review` → `approve` and one `delegate` → `approve`.

## Methodological limits

- Balanced synthetic sample, 20 per class.
- ChatGPT GPT-6.2 annotated in-conversation; no external batch API inference was called.
- One LLM pass only; no human expert validation or inter-rater kappa.
- High agreement with synthetic labels does not prove real-world CRM realism.
- Naturalness is weak (2.51/5) despite high classification accuracy.

## Files

- `GEN010_11C_LLM_vs_GroundTruth_Report.xlsx` — downloadable conversation artifact.
- `GEN010_11C_LLM_vs_GroundTruth_Report.json` — downloadable conversation artifact.
- `docs/GEN010_11C_CHATGPT_LLM_VS_GROUND_TRUTH.md` — committed report.

## Next step

GEN-010.12: renderer quality improvement. Address naturalness and semantic separation of request_information, delegate and complete_task. Re-run a fresh blind holdout after changes; do not reuse this opened sample for blind validation.
