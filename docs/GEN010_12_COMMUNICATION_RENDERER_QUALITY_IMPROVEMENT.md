# GEN-010.12 — Communication Renderer Quality Improvement

**Status:** IMPLEMENTED — structural QC PASS; text diversity REVIEW  
**Renderer:** 1.1.0  
**Branch:** feature/generator-v4-organization-engine

## Objective

Improve communication naturalness and make the three frequently confused event classes semantically distinct: `request_information`, `delegate`, and `complete_task`.

## Changes

1. Removed generic system-log style openers and closers from rendered message bodies. Event-specific text is now rendered directly.
2. Added dedicated action-oriented template bank for:
   - `request_information`: asks for missing source information/documents; explicitly distinguishes information gathering from task assignment.
   - `delegate`: explicitly assigns a named organizational role as executor and asks for a result; does not imply task completion or final approval.
   - `complete_task`: states that previously assigned work has been completed and its result handed over; does not create a new assignment.
3. Used the actual addressee role label from the organization model in assignment/completion text where available.
4. Preserved observable-only rendering: hidden decision outcomes and scenario context are not inserted into message text.
5. Bumped renderer version to `1.1.0`.
6. Added regression tests for distinct action semantics, removal of generic boilerplate, source attribution, and existing privacy constraints.

## CI and QC

- Process model QC: SUCCESS — https://github.com/Dmitriy1105/LPR_26/actions/runs/45510409934
- Renderer structural validation: PASS
- Renderer test suite: PASS (12 tests)
- Rendered communications in in-memory audit: 6,440
- Structural validation errors: 0
- Text diversity: REVIEW, not PASS
- Minimum normalized body uniqueness ratio by event class: 0.0063
- High-similarity pair ratio (Jaccard >= 0.85): 0.141508
- Generation authorization: false
- Bulk generation: false

## Interpretation

The change removes repeated generic boilerplate and improves the semantic separation of request, assignment, and completion. The test suite confirms the required action language and structural lineage.

However, the renderer still uses a finite deterministic template bank. Lexical diversity remains insufficient (minimum uniqueness ratio 0.63%; high-similarity pairs 14.15%). The audit deliberately reports `text_diversity_status=REVIEW` while keeping structural QC separate; a structural PASS must not be interpreted as text-quality PASS.

No new human naturalness score has been collected after this change. The previous 2.51/5 score is a pre-change baseline and must not be presented as the new score.

## Next actions

1. Use a fresh blind 220-record pack built from renderer 1.1.0; do not reuse the opened GEN-010.11C sample.
2. Re-annotate the new pack with ChatGPT in a blind pass and lock the output hash before opening its answer key.
3. Compare event classification and text-quality ratings with the prior baseline.
4. Expand semantic paraphrase diversity without adding unsupported facts or generic filler.
5. Keep bulk generation disabled until naturalness and semantic-diversity gates are accepted.
