# Synthetic Bank Dataset v3.1 — Bitrix24 REST-compatible multiparty data

This release improves the reproducible synthetic-data extension without replacing the existing v1/v2 datasets. Version 3.1 adds deterministic, event-specific text generation while preserving the normalized v3 data model and the legacy Bitrix24 REST fixture contract.

## Compatibility guarantees

- The normalized bank_ml_v2 source is reused by generate_synthetic_bank_v3.mjs.
- `metadata.generatorVersion` identifies the text-generation implementation (`3.1.0`); `metadata.version` remains `3` for compatibility with the fixture exporter.
- Existing calls, emails, meetings, opportunities, and CRM contact identifiers remain compatible.
- New decision meetings and internal client messages use the existing normalized event structures.
- Calls, emails, meetings, decision-meeting minutes and internal messages receive deterministic contextual text variants.
- Text variants use the event's existing topic, date, direction, disposition, sentiment and participant context; no event records or REST field names are added or removed.
- Bitrix24 fixtures retain the same legacy REST response envelope and field names:
  - crm.item.list
  - crm.activity.list
  - tasks.task.list
- Multiparty activity participants use the existing COMMUNICATIONS array with ENTITY_ID and ENTITY_TYPE_ID.
- No custom REST fields are introduced for participant linkage.

## New files

- scripts/generate_synthetic_bank_v3.mjs — deterministic v3.1 dataset generator.
- scripts/generate_bitrix24_contract_fixtures_v2.mjs — legacy REST v1 response fixtures with multiparty communications.
- src/data/synthetic/bank_ml_v3.json — generated normalized dataset.
- src/data/synthetic/bank_ml_v3_ground_truth.json — isolated evaluation labels. This file must never be passed into NLP feature extraction.
- src/data/bitrix24_contract_v2/ — paginated REST response fixtures.

## Text quality and duplicate control

- Text generation is deterministic for a fixed seed.
- The test suite checks that each REST activity type has at least 95% exact-text uniqueness after whitespace/case normalization.
- Exact duplicates are not silently deleted: each activity remains a separate event. Downstream NLP must distinguish repeated wording from independent evidence and avoid multiplying confidence solely because the same template recurs.
- Exact-text uniqueness is not semantic uniqueness. Similar meanings can still appear in different wording and require NLP-level evidence grouping.

## Run locally

    node scripts/generate_synthetic_bank_v3.mjs
    node scripts/generate_bitrix24_contract_fixtures_v2.mjs
    node --test tests/synthetic_bank_v3.test.mjs

## Important methodological notes

- Co-participation is not proof of influence, hierarchy, or decision authority.
- Ground-truth labels are evaluation-only and must be kept separate from NLP inputs.
- These fixtures reproduce a subset of Bitrix24 legacy REST response conventions; they are not a live portal and do not replace validation against the target Bitrix24 account and API version.
- All generated records are fictional.
