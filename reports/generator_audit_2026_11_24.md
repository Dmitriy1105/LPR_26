# LPR_26 — Generator v3.2.3 / v3.3.0 evidence-based audit

Date: 2026-11-24. **Read-only audit of original branches**; findings below generated from fetching all thirteen committed CRM activity pages in each branch. This file documents observations, not a newly executed end-to-end generator workflow.

## Source commits and scope
- v3.2.3: `feature/synthetic-bank-v3.2.3-nlp-diversity`, commit `c093bd52b5603596c633cc7c238e5d8f1f0d76ae`.
- v3.3.0: `feature/synthetic-bank-v3.3.0-compatible-nlp`, commit `aa17dd9f01ce2bad8d08f7f542654c909625e8b9`.
- Published UI data are on `main`, distinct from these development fixtures. They should not be compared as though they were the same dataset.
- Dataset path for **both** versions: `src/data/bitrix24_contract_v3_2_3/`. The v3.3.0 fixture root retains the older directory name; trust manifest `generatorVersion`, not directory name or README alone.

## Independently checked file-based invariants
| Metric | v3.2.3 | v3.3.0 |
|---|---:|---:|
| Activities, across 13 pages | 630 | 630 |
| Activity types: meeting (1) | 126 | 126 |
| Activity types: call (2) | 180 | 180 |
| Activity types: email (4) | 324 | 324 |
| Unique normalized descriptions (lowercase, collapse whitespace, trim) | 625 | 630 |
| Extra repeated descriptions | 5 | 0 |
| Multi-contact CRM activities | 90 | 90 |
| Total COMMUNICATIONS refs | 749 | 749 |

v3.3.0 fixture inspection independently verified: 630 distinct activity IDs (zero duplicate IDs), 630 nonempty descriptions, 0 missing references to 30 contact IDs, 540 single-contact and 90 multi-contact activities (66 with 2, 19 with 3 and 5 with 4 references), all 630 descriptions split into 4 segments, 54 distinct co-participant pairs. Non-activity files separately fetched: 1 company, 30 contacts, 18 deals, 44 invoices, 44 tasks; 767 total records. This confirms file contents/counts and reference integrity, not chronological or semantic realism, independent regeneration, or whole-entity relational consistency.

## Findings
### G-01 HIGH — lexical uniqueness mistakenly treated as text quality
The v3.3.0 generator inserts `(обращение <ID>)` and picks from only 8 action phrases, 6 openings, 6 details and 6 endings with modulo operations on the activity ID. Every description is unique, but this check cannot detect semantic duplicates, template fingerprints, scenario contradictions or action coverage skew. The existing version's 100% exact uniqueness is therefore insufficient evidence of realistic language.

### G-02 CRITICAL — person-level attribution missing from synthetic ground truth
`src/data/nlp_ground_truth_v3_3_0/action_ground_truth.json` has exactly 630 annotations. All 630 have `actor_contact_id: null`, `actor_identity_verified: false`, and `attribution_status: unspecified_client_representative`. The text's `представитель клиента` is not uniquely attributable to any named participant. Role/participant co-occurrence must not become evidence of speaker, subject, decision authority, support or influence. The v3.3.0 checkpoint reports 0 verified personal signals in NLP 12; separately, signal count 2344 is a quantity not a precision score.

### G-03 HIGH — incomplete published UI provenance, not disproved source multiparty data
The `main` UI activity index was reported to have exactly one `contact_ids` item on each of 540 published entries, whereas both generator branches preserve 90 multiparty activities and 749 total COMMUNICATIONS refs. These are **different datasets and schemas**; no source-to-UI mapping/provenance proof yet. The UI may synthesize graph edges from another source; verify actual build path, pair-level provenance and null semantics before assigning relationships.

### G-04 HIGH — changing texts in existing v3.2.3 path damages reproducibility
v3.3.0 overwrites `src/data/bitrix24_contract_v3_2_3/activities/*.json` in place, retains `README.json` with version 3.2.3, and updates the manifest to v3.3.0. The data are distinguishable by Git ref and manifest, but ambiguous when exported without the Git SHA.

### G-05 HIGH — generated label is not independent NLP evaluation
The v3.3.0 annotation source itself is `synthetic_generator_v3.3.0`; it describes the injected phrase, not human-validated independent relationship labels. A held-out, manually reviewed evaluation set is still needed, split by scenario/template to prevent leakage. Include explicit negatives, contradictory events, negations, multiple participants, role changes, disputed decisions and cross-department interactions.

### G-06 MEDIUM — NLP 3.3.1 evaluated on detached demonstration scenarios
The branch `feature/nlp-influence-v3.3.1-mvp` extractor iterates `nlp_enrichment_v3_3_1/scenarios.json`, not all 630 fixture descriptions; it uses four exact verb patterns, demands actor and target name in strict order, and returns `influence_verified: false`. Do not treat these matches as confirmed influence edges.

## Acceptance gates before scoring or model training
1. Preserve immutable versioned artifacts and record commit SHA, seed, data contract version and checksums in a manifest.
2. Verify all 767 records across six entities and 13 activity pages, uniqueness, required fields, referential integrity, timestamp ordering, topic distributions, participant validity and graph edge provenance.
3. Report **both** normalized lexical uniqueness **after removing IDs/dates** and semantic similarity measured within and between activity types; also count templates, action coverage, negations, classes and role combinations.
4. Separate `participants`, `speaker`, `actor`, `target`, `grammatical_subject`, `decision_authority`, and `stance_toward_vendor` in a provenance-bearing evidence schema. Never infer verified actors from membership, role mentions, owners or contextual co-occurrence.
5. Add an independently reviewed and held-out gold dataset with unknown/ambiguous cases and explicit negatives; calculate class-wise precision, recall and F1 against that set. Generator-created labels are suitable as synthetic training labels only, not independent evidence of accuracy.
6. Defer multi-factor LPR scores until confidence, missingness and calibration are explicitly represented. Keep authority, influence and vendor loyalty separate; no edge from shared meeting alone.

## Evidence links
- Generator v3.2.3: https://github.com/Dmitriy1105/LPR_26/blob/feature/synthetic-bank-v3.2.3-nlp-diversity/scripts/generate_bitrix24_contract_v3_2_3.mjs
- Generator v3.3.0: https://github.com/Dmitriy1105/LPR_26/blob/feature/synthetic-bank-v3.3.0-compatible-nlp/scripts/generate_bitrix24_contract_v3_3_0.mjs
- Ground truth: https://github.com/Dmitriy1105/LPR_26/blob/feature/synthetic-bank-v3.3.0-compatible-nlp/src/data/nlp_ground_truth_v3_3_0/action_ground_truth.json
- Older structural audit: https://github.com/Dmitriy1105/LPR_26/blob/feature/synthetic-bank-v3.2.3-nlp-diversity/reports/v3_2_3/structural_audit.json
- Historical 3.3.0 NLP checkpoint: https://github.com/Dmitriy1105/LPR_26/blob/feature/synthetic-bank-v3.3.0-compatible-nlp/docs/checkpoints/2026-11-23_LPR_26_v3.3.0_NLP_checkpoint.md

## Work status
**Complete:** static file-level counts, descriptions, participant refs, 13-page scope, ground-truth actor audit; core code review.
**Not completed:** regenerating all fixtures from scratch, independent semantic embeddings/TF-IDF, detailed chronology and full dependency graph, published UI source-to-edge mapping, human gold labeling, model quality benchmarking and browser UI tests. Do not mark these as PASS.

