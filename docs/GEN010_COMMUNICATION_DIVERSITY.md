# GEN-010 — Contextual Communication Diversity

**Status:** IMPLEMENTED — CI validation passed on the implementation commit before the version-only bump; final full CI rerun is required for the version bump.  
**Branch:** `feature/generator-v4-organization-engine`  
**Scope:** synthetic CRM communication rendering only. NLP remains a separate downstream analysis layer.

## Objective

Increase contextual diversity of generated CRM messages without changing the scenario event stream, decision authority, event attribution, communication-to-event coverage, or Ground Truth projection.

## Changes

1. Added `scripts/communication_context_v1.mjs`.
   - Selects deterministic context details from the deal scope: `technical`, `budget`, or `commercial`.
   - Uses six context variants per scope.
   - Uses event-specific introductory wording for the ten event types.
   - Selection is deterministic for a given seed and event ID.

2. Updated `scripts/scenario_communication_generator_v1.mjs`.
   - Communication descriptions now include an event-appropriate context clause.
   - Existing event-to-channel mapping and author/recipient/deal/source-event references remain unchanged.
   - Communication generator version: `1.1.0`.

3. Strengthened `scripts/test_generator_text_diversity_v1.mjs`.
   - Correct Unicode-aware normalization for Russian text.
   - Exact normalized body uniqueness.
   - Token Jaccard similarity audit within event type.
   - Minimum 100 unique contextual bodies per seed.
   - At least two body variants per event type.
   - Deterministic replay and cross-seed variation.
   - Ground Truth metadata leakage guard.

4. Updated the QC workflow trigger paths for the new context module.

## Measured results

From CI run #193, implementation commit `74366d11956beacf46e39227f70b3ac5c2bc2dcf`:

- Full CI: **SUCCESS**.
- Eight deterministic seeds in the consolidated evaluation.
- Events: **1,959**.
- Communications: **1,959**.
- Ground Truth records: **1,959**.
- Event types: **10**.
- Structural integrity, event/communication coverage, semantic projection, Ground Truth consistency, deterministic replay and seed variation: **PASS**.
- Text diversity diagnostic: **0.7987**, compared with **0.3242** before contextual enrichment.
- Weighted diagnostic index: **0.9799** (not a certification or acceptance score).

Unique contextual body counts by seed in the consolidated evaluation:

| Seed | Unique bodies | Communications |
|---:|---:|---:|
| 0 | 193 | 240 |
| 1 | 196 | 249 |
| 7 | 196 | 237 |
| 19 | 202 | 243 |
| 42 | 203 | 252 |
| 2026 | 189 | 246 |
| 99173 | 190 | 237 |
| 4294967295 | 195 | 255 |

## Interpretation and limitations

The diversity increase is a measured exact-text result produced by combining existing event-specific message templates with scope-specific context. It does **not** prove that every message is naturally phrased, factually realistic, or semantically appropriate. Jaccard is a lexical similarity diagnostic, not a human semantic review.

Still outstanding:
- independent review of communication meaning and conversational coherence;
- verification that every contextual statement is supported by the scenario's actual deal attributes;
- executable BPMN trace equivalence for the generated scenario;
- distributional calibration against an independently specified synthetic business profile.

## Next stage

**GEN-011 — BPMN Execution Trace Integration.** Establish a single trace contract between scenario generation and the executable BPMN/DMN engine. Compare event order, actor assignment, authority decisions, branch outcomes, and process closure. Do not mark GEN-011 complete based only on schema compatibility or the existing independent BPMN tests.
