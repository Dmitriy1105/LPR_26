# Synthetic Bitrix24 REST dataset v3.2.1

- Generator: `scripts/generate_synthetic_bank_v3_2_1.mjs`
- Parent version: `3.2.0`
- Seed: `20261123`
- REST profile: `legacy-rest-v1`
- Data root: `src/data/bitrix24_contract_v2`

## Scope

The generator rewrites only `DESCRIPTION` for the 324 email-type activities (`TYPE_ID=4`). Calls and meetings remain unchanged. Activity IDs, `COMMUNICATIONS`, REST response fields, page structure, contact references, and entity counts are preserved.

Expected distribution: 180 calls, 324 emails, 126 meetings; 630 activities total. The dataset also retains 1 company, 30 contacts, 18 deals, 44 invoices, and 44 tasks.

All records are fictional synthetic examples. They are not evidence about real customers or decision makers. The output is suitable for development and exploratory NLP testing, not as validated ground truth.

## Reproduce

From the repository root, using Node.js:

```bash
node scripts/generate_synthetic_bank_v3_2_1.mjs
node --test tests/synthetic_bank_v3_2_1.test.mjs
```

The generator is deterministic for seed `20261123`. It updates activity pages, manifest metadata, and `generation_report_v3_2_1.json`.

## EDA Cell 2 source

Keep the branch and URL in sync:

```python
OWNER = "Dmitriy1105"
REPO = "LPR_26"
BRANCH = "feature/synthetic-bank-v3.2.1-email-diversity"
DATA_ROOT = "src/data/bitrix24_contract_v2"
BASE_URL = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{DATA_ROOT}/"
```
