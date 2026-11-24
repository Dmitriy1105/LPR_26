# GEN-010.11B.1 — Blind LLM Semantic Annotation Protocol

**Status:** SPECIFICATION_STARTED — fresh holdout required  
**Parent stage:** GEN-010.11B  
**Repository branch:** feature/generator-v4-organization-engine

## Purpose

Run an actual language-model semantic annotation pass over a fresh, blinded sample of generated CRM communications, then compare the locked annotations with the synthetic Ground Truth.

## Why a fresh holdout is mandatory

The earlier 220-record sample and its restricted answer key were opened during GEN-010.11B baseline analysis. That sample is no longer suitable for a claim of blind annotation by the same evaluation process. Do not relabel it as a fresh blind experiment.

## Protocol

1. Generate a new deterministic sample of 220 communications from the corrected Generator v4.0 renderer, with a new seed/sample identity distinct from GEN-010.11A.
2. Create two artifacts: (a) blinded text-only annotation pack; (b) restricted answer key. The answer key must not be included in the annotation input or exposed to the annotator.
3. Ensure the blinded pack excludes event_type, source_event_id, source_ref, organization_id, deal_id, contact IDs, timestamps, and any scenario metadata that reveals the intended class. Keep only review_id, channel, record_format, subject, and body.
4. Run an actual LLM inference pass. Record provider/model identifier, model version if exposed, prompt version, timestamp, temperature/decoding settings if configurable, and input/output hashes. Do not describe keyword rules, heuristics, or this assistant's unaided manual reasoning as a separate LLM inference call.
5. For each record, emit one primary event class from the 11 contract classes or `unclear`, confidence (0–1), a short text-grounded rationale, clarity/naturalness/factual-support ratings (1–5), and unsupported-claim notes.
6. Validate exactly 220 unique review IDs, valid labels, rating ranges, and no answer-key fields in model input/output.
7. Lock the annotation JSON and record SHA-256 before opening the answer key.
8. Open the answer key only after the lock. Compute accuracy, per-class precision/recall/F1, macro-F1, confusion matrix, and channel breakdown. Compare with the existing rule-based baseline on the same held-out IDs only if that baseline is independently run on the new sample.
9. Report the balanced-sample limitation. Do not claim that agreement with synthetic Ground Truth proves real-world CRM realism.

## Event classes

request_information, delegate, complete_task, review, recommend, object, revise, unit_approval, approve, reject, close. The annotator may additionally return unclear.

## Required output files

- `reports/gen01011b1_blind_llm_annotations.json`
- `reports/gen01011b1_blind_llm_manifest.json`
- `reports/gen01011b1_ground_truth_comparison.json` (created only after annotation lock)
- `docs/GEN010_11B1_BLIND_LLM_SEMANTIC_ANNOTATION.md`

## Acceptance gates

- Fresh sample identity and seed verified.
- Blind pack contains 220 unique records and no label leakage.
- Actual LLM inference provenance is recorded; no simulated or rule-based substitute.
- Annotation artifact hash is recorded before key release.
- Ground Truth comparison runs only after lock.
- No human-expert validation or independent inter-rater agreement is claimed.

## Current blocker

The current conversation has no independently callable LLM inference endpoint or model-provider credentials exposed for batch execution. ChatGPT can provide semantic judgments in conversation, but that is not a reproducible external batch-inference run with a verifiable model-call log. Do not fabricate provider logs or claim a batch LLM run. The next implementation task is to prepare the fresh blinded pack and an inference adapter, then run it through an explicitly configured model endpoint.


## 2026-11-25 implementation update — fresh pack built

- Fresh sample ID: `GEN01011B1-SEED-20261125`.
- Scenario seed: `42`; deterministic sample-selection seed: `20261125`.
- 220 records: exactly 20 per each of 11 event classes, distributed across all 20 organizations.
- The LLM classification input was tightened to **review_id, subject, body only**. Channel and record_format were removed from model input because the generator's event-to-channel mapping can act as a label shortcut.
- Blind-pack audit: PASS; 220 unique IDs; no Ground Truth fields; no internal scenario markers; answer key separate.
- Blind-pack SHA-256: `86e95f4219ad87ed2e92416e53b0d9ab1374c75a78159aa780e38489c2251f61`.
- CI run: https://github.com/Dmitriy1105/LPR_26/actions/runs/45506756588
- Reviewer-visible artifact ID: `14972574525`.
- Restricted answer-key artifact ID: `14973970286`; not opened or downloaded during this step.
- OpenAI-compatible inference adapter added at `scripts/generator_v4_gen01011b1_llm_adapter_v1.py`.

**Current status:** fresh sample built and validated. Actual LLM inference has not run because no model-provider endpoint/model credentials are configured in the repository environment. Do not open the restricted key until the annotation JSON is completed and locked.
