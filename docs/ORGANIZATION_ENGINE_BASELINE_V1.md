# Organization Engine Baseline v1.0

**Status:** PASS  
**QC source:** GitHub Actions Process model QC #116  
**Commit tested:** `ae884a5d875281a8bb713e5338a9ab8920ace900`  
**Branch:** `feature/generator-v4-organization-engine`  
**Generator configuration:** seed=42, count=5  

## Verified results

| Organization | Units | People | Role records | Result |
|---|---:|---:|---:|---|
| ORG-0001 | 9 | 30 | 30 | PASS |
| ORG-0002 | 9 | 31 | 31 | PASS |
| ORG-0003 | 9 | 40 | 40 | PASS |
| ORG-0004 | 9 | 34 | 34 | PASS |
| ORG-0005 | 9 | 37 | 37 | PASS |
| **Total** | **45** | **172** | **172** | **PASS** |

## Nine baseline checks

- Deterministic generation
- Unique organization identifiers
- Required department coverage
- Sales department coverage
- Separate security and information-security units
- Complete role coverage
- Competencies start without unsupported evidence
- Authority and influence are not inferred by default
- Cross-module compatibility with empty authority, delegation, organizational-change and event ledgers

All nine checks passed; failed checks: none. The test suite also reports 5 positive baseline cases across 5 organizations.

## Required departments

Sales, finance, technical, procurement, legal, project office, security, and information security. Each generated organization also has a headquarters root unit.

## Scope and limitations

This baseline certifies the deterministic synthetic organizational fixture and the listed structural/cross-module QC checks. It does not certify real-world HR data, legal validity of authority documents, production BPMN/DMN execution, full event-log equivalence, or end-to-end CRM integration. Authority, competencies, influence and event ledgers require separately sourced evidence before operational use.

## Reproducibility

Run `python scripts/organization_engine_qc_v1.py` and `python scripts/test_organization_engine_qc_v1.py` in the repository environment. The machine-readable report is `reports/organization_engine_baseline_v1.json`.
