# Synthetic Bank Dataset v3.2 — Scenario-based communication generation

## Purpose

v3.2 is a controlled experiment built on the v3.1 structural generator. It changes communication text composition while retaining the v3 normalized data model and the existing legacy Bitrix24 REST fixture exporter.

## Compatibility

- `generateV3` from v3.1 remains the structural source.
- `metadata.version` remains `3` for compatibility with the fixture exporter.
- `metadata.generatorVersion` is `3.2.0`.
- Calls, emails, meetings, decision meetings, internal client messages, event IDs, contact IDs, opportunity IDs, participant references and event index are retained from the v3.1 generation path.
- The REST fixture contract remains `legacy-rest-v1` with the same `COMMUNICATIONS` shape.
- The target REST activity count remains 630 and is asserted by tests.
- Ground truth remains separate from NLP inputs.

## v3.2 text changes

Communication text is composed from deterministic, event-specific scenario fragments:

- topic profile and evidence requirements;
- participant role and contact context;
- sentiment / position;
- email direction;
- call disposition;
- meeting agenda and participants;
- internal message intent and requested action.

The generator avoids the v3.1 generic gender-placeholder pattern in internal messages. It does not add or remove CRM entities or activity records.

## Reproducibility

Default seed: `20261122`.

Run:

    node scripts/generate_synthetic_bank_v3_2.mjs
    node scripts/generate_bitrix24_contract_fixtures_v2.mjs
    node --test tests/synthetic_bank_v3_2.test.mjs

## Validation

Tests cover:

- deterministic generation for a fixed seed;
- normalized collection compatibility;
- non-empty scenario text;
- no `(а)` gender placeholders in generated communication text;
- exactly 630 REST activities;
- valid contact references in `COMMUNICATIONS`;
- at least 95% exact-text uniqueness per REST activity type.

The 95% threshold is a regression guard, not a semantic-diversity metric.

## Interpretation limits

- TF-IDF similarity measures lexical overlap, not semantic equivalence.
- Scenario variety does not prove realistic human behavior.
- Co-participation does not prove influence or decision authority.
- Ground-truth labels must not enter NLP features or inference context.
- All records are fictional and are not evidence about real customers.
