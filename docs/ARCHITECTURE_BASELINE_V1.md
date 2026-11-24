# Architecture Baseline v1.0 — restricted profile candidate

Status: CANDIDATE / FINAL CI REQUIRED.
Verified implementation: 7cfe1b60a2110ed53bd3032b19bb983e2571f13a (run 45425761757).
Regression evidence: 92bee25cee0729f12b51f72008d96bf3f99ab45a (run 45426520053).
Reported cumulative checks: 1197; not an independently deduplicated coverage count.

## Scope
Deterministic simulation of the fixed demonstration organization using restricted BPMN and DMN, declarative process bindings, authoritative role and budget checks, optional task assignment, logical event trace, current and historical replay. No general OMG execution conformance, production CRM generation or real-world NLP validity claim.

## Architecture
BPMN process models -> restricted execution kernel -> DMN decision tables and organizational policy adapters -> event trace -> replay and QC.
Authoritative execution is the required future generator boundary. Low-level executor is for model tests only. Legacy runners are regression references, not production interfaces.
Task assignment does not transfer decision authority. DMN evaluation is not evidence of human enactment or social influence.

## Acceptance and open issues
See reports/architecture_defect_registry.json v1.3 and reports/architecture_qc_report.json. Seven closed, seven partial, one limitation.
ARCH-004/011: independent full node and actor audit and physical chronology.
ARCH-005: legacy runners and remaining duplicate bindings.
ARCH-006: expanded malformed configuration coverage.
ARCH-013/014: generator integration, temporal grants and dynamic delegation.
ARCH-015: archived execution environment and independent full trace semantics.
ARCH-012: restricted supported profile.
No open item is waived by this candidate. Scope approval and successful CI on the candidate revision are required before tagging.

## Next milestone
Organization Engine: multiple organizations, temporal authority, role and hierarchy validation, delegation policy and task chronology. Then relationship, simulation, communication, ground truth and CRM projection engines. Keep gold labels separate from NLP input and predictions.
