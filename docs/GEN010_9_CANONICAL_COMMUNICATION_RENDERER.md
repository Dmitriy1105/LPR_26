# GEN-010.9 — Canonical Communication Renderer

**Status:** PASS — structural, attribution, observable-only, semantic-marker and lexical-diversity QC  
**Branch:** `feature/generator-v4-organization-engine`  
**CI:** [Process model QC #45493077525 — SUCCESS](https://github.com/Dmitriy1105/LPR_26/actions/runs/45493077525)

## Implemented

- `scripts/generator_v4_communication_renderer_v1.py` — deterministic renderer consuming only `observable_events` and canonical organization metadata.
- `scripts/test_generator_v4_communication_renderer_v1.py` — regression suite for event coverage, deterministic replay, channels, attribution, missingness, speaker uncertainty, hidden-truth isolation, semantic markers and body diversity.
- `scripts/generator_v4_communication_renderer_audit_v1.py` — per-event-type lexical diversity and structural QC report.
- `scripts/generator_v4_scenario_engine_v1.py` — observable close-event context sanitized so the hidden decision outcome is not repeated in the model-facing projection.
- `.github/workflows/process-model-qc.yml` — renderer audit and tests included in CI.

## QC world and communication counts

Seed 42; 20 organizations; 800 deal episodes; 6,440 observable events and 6,440 communications. One communication is rendered for every observable event.

| Channel | Communications |
|---|---:|
| Email | 2,600 |
| Call summary | 1,000 |
| Meeting record | 2,840 |
| **Total** | **6,440** |

Event-type coverage:
- request_information: 800
- delegate: 800
- complete_task: 800
- review: 1,000
- recommend: 800
- object: 200
- revise: 200
- unit_approval: 240
- approve: 680
- reject: 120
- close: 800

## Quality measurements

- Unique source-event coverage: 6,440 / 6,440.
- Attribution and chronology reconciliation: PASS.
- Observable missingness preserved: 668 communication records carry one or more missing-field markers.
- Fabricated speaker turns: 0.
- Minimum normalized body uniqueness ratio across event types: **0.5925**.
- Within-event-type high lexical similarity pairs (Jaccard >= 0.85) / all compared pairs: **0.001374**.
- Semantic marker checks against observable event types: PASS.
- Same-seed deterministic replay: PASS.
- CI run: SUCCESS.

Lexical uniqueness and Jaccard are diagnostics, not proof of semantic realism. The acceptance test enforces a minimum body uniqueness ratio of 0.55 per event type and a high-similarity pair ratio no greater than 0.005.

## Ground Truth isolation correction

The source event's original `close` context note included the hidden decision outcome (approved/rejected). Passing it through unchanged would have leaked the target label into NLP-facing text.

The observable projection now substitutes the neutral note `Deal episode closed` before applying the configured missingness mask. The original event and decision outcome remain in evaluation-only Ground Truth. Regression tests verify that observable close-event context and rendered closure communications contain neither outcome token.

The renderer itself has no Ground Truth parameter and receives only observable events plus organization metadata. It does not receive authority grant references or hidden decision outcomes.

## Interpretation and limitations

1. This is a deterministic, rule/template-based renderer with compositional paraphrase variation. It is **not** a trained language model and does not claim learned natural-language generation.
2. Call records are summaries of observable event types, not fabricated verbatim transcripts. `speaker_contact_id` remains null because turn-level speaker annotations are unavailable.
3. The renderer preserves author, participants, addressee, event timestamp, source reference, channel, decision scope, and missingness metadata.
4. Text diversity is substantially improved, but lexical metrics alone cannot establish realistic business language, factual entailment, or downstream NLP utility.
5. Financial authority bands and monetary evidence remain an open contract gap from GEN-010.8.
6. No persistent CRM fixture or NLP corpus was written. `generation_authorized=false` and `bulk_generation_enabled=false` remain unchanged.

## Next stage — GEN-010.10

Perform semantic and attribution audit of rendered communications against observable event context:
- verify that each body asserts no facts beyond its source event and visible context;
- test role, author, addressee and participant consistency;
- check that objections, revisions, recommendations, unit approvals and final decisions are not conflated;
- validate channel-specific format constraints;
- assess text realism with independent review and NLP task-oriented tests;
- retain Ground Truth only as an evaluation oracle, never as renderer input.

Only after this audit should the team consider a separate authorization review for persistent dataset generation.
