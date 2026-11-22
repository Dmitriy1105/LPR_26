# Synthetic Bank Dataset v3 — Bitrix24 REST-compatible multiparty data

This release adds a reproducible synthetic-data extension without replacing the existing v1/v2 datasets.

## Compatibility guarantees

- The normalized bank_ml_v2 source is reused by generate_synthetic_bank_v3.mjs.
- Existing calls, emails, meetings, opportunities, and CRM contact identifiers remain compatible.
- New decision meetings and internal client messages use the existing normalized event structures.
- Bitrix24 fixtures retain the same legacy REST response envelope and field names:
  - crm.item.list
  - crm.activity.list
  - tasks.task.list
- Multiparty activity participants use the existing COMMUNICATIONS array with ENTITY_ID and ENTITY_TYPE_ID.
- No custom REST fields are introduced for participant linkage.

## New files

- scripts/generate_synthetic_bank_v3.mjs — deterministic v3 dataset generator.
- scripts/generate_bitrix24_contract_fixtures_v2.mjs — legacy REST v1 response fixtures with multiparty communications.
- src/data/synthetic/bank_ml_v3.json — generated normalized dataset.
- src/data/synthetic/bank_ml_v3_ground_truth.json — isolated evaluation labels. This file must never be passed into NLP feature extraction.
- src/data/bitrix24_contract_v2/ — paginated REST response fixtures.

## Run locally

    node scripts/generate_synthetic_bank_v3.mjs
    node scripts/generate_bitrix24_contract_fixtures_v2.mjs
    node --test tests/synthetic_bank_v3.test.mjs

## Important methodological notes

- Co-participation is not proof of influence, hierarchy, or decision authority.
- Ground-truth labels are evaluation-only and must be kept separate from NLP inputs.
- These fixtures reproduce a subset of Bitrix24 legacy REST response conventions; they are not a live portal and do not replace validation against the target Bitrix24 account and API version.
- All generated records are fictional.
