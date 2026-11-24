# LPR_26 checkpoint — GEN-010.11B.1

**Date:** 2026-11-25  
**Repository:** Dmitriy1105/LPR_26  
**Branch:** feature/generator-v4-organization-engine  
**Base commit before this checkpoint:** 5ff569619322a19a6f16b8db56b70f03260369ae  
**Documentation commit:** 2f0ef7f14898bce1c6cbf2c416fc18b9fd80b16e

## Completed

- GEN-010.11B automated baseline vs Ground Truth was calculated for 220 records.
- Critical provenance correction recorded: the previous annotation file was produced by a scripted keyword/rule-assisted process, not a verified actual LLM inference pass.
- The baseline must not be represented as LLM expert evaluation or human expert review.
- A fresh blind LLM semantic annotation protocol was added:
  `docs/GEN010_11B1_BLIND_LLM_SEMANTIC_ANNOTATION.md`.

## Important methodological boundary

The previous 220-record pack and restricted answer key were opened during the baseline analysis. That sample must not be reused to claim a blind LLM experiment. A fresh sample and a new restricted answer key are required.

## Next actions

1. Build a fresh 220-record sample from the corrected Generator v4.0 renderer using a new seed/sample identity.
2. Validate the blind pack for leakage; keep answer key separate.
3. Configure an actual LLM inference endpoint and record provider/model/version, prompt version, run metadata and hashes. Do not fabricate inference provenance.
4. Run semantic annotations, validate 220 unique IDs, then lock the annotation JSON and record SHA-256.
5. Only after the lock, open the new answer key and compute Accuracy, per-class Precision/Recall/F1, Macro-F1, confusion matrix and channel breakdown.
6. Compare with a rule-based baseline evaluated on the same fresh held-out IDs.

## Status

**GEN-010.11B.1:** SPECIFICATION_STARTED — awaiting fresh holdout pack and configured LLM inference endpoint.  
No new LLM batch inference has been run. No human expert validation is claimed.


## 2026-11-25 execution update

### Fresh sample generated and validated

- Sample: `GEN01011B1-SEED-20261125`.
- Scenario seed 42; selection seed 20261125.
- 220 unique records, 20 per class, spread across 20 organizations.
- Model-visible input contains only `review_id`, `subject`, `body`. Channel and record_format were deliberately removed to prevent shortcut learning from the deterministic event/channel mapping.
- Audit: PASS — all 6 validation checks passed, no Ground Truth fields, no internal scenario labels.
- Blind pack SHA-256: `86e95f4219ad87ed2e92416e53b0d9ab1374c75a78159aa780e38489c2251f61`.
- CI: https://github.com/Dmitriy1105/LPR_26/actions/runs/45506756588 (SUCCESS).
- Public blind artifact: `14972574525`.
- Restricted key artifact: `14973970286` (not opened).

### Added implementation

- `scripts/generator_v4_gen01011b1_blind_pack_v1.py`
- `scripts/generator_v4_gen01011b1_llm_adapter_v1.py`
- `scripts/test_generator_v4_gen01011b1_blind_pack_v1.py`
- `.github/workflows/gen01011b1-blind-llm.yml`

### Remaining blocker

The adapter is implemented but actual inference is not run: repository environment has no configured `LLM_API_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`. Configure these as repository Actions secrets/variables (do not paste API keys into chat), then run the adapter against the blind artifact. Lock annotation output and SHA-256 before downloading/opening restricted answer key artifact `14973970286`.
