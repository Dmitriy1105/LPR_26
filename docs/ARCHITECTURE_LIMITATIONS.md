# Architecture limitations — baseline candidate

Status: REVIEW_REQUIRED. Verified CI run 45407656802, commit 9f6cd33. Passing tests are evidence for the tested profile only, not OMG execution conformance.

## Acceptance gates

- Close ARCH-004, 005, 011, 013 and 015 or explicitly narrow the baseline scope and obtain approval.
- Add negative tests for missing, duplicated and reordered nested events, inconsistent actor evidence, unsupported expressions and direct budget authority bypass.
- Verify registry and model hashes, exact process replay and complete transition provenance.
- Document scoped QName limitations and supported FEEL/BPMN subset. No claim of universal execution.
- Keep dynamic delegation, task assignment, relationship simulation and communication generation as separate future milestones.
- Run complete CI on the exact candidate commit before tagging a baseline.

The current fixture uses one organization and specialized composite runners. Synthetic ground truth is not independent evidence of real-world NLP accuracy. No final baseline is accepted by this document.

## Final regression candidate

Verified run 45425761757 at 7cfe1b60. Seven defects closed, seven partial, one limitation. Proposed scope: deterministic restricted BPMN/DMN simulation of the fixed demo organization, authoritative budget and role checks, optional task assignment, logical trace and trusted historical replay. Not a general BPMN engine, not a production generator, not independent real-world validation. Historical Python environment not archived; oracle revised against existing protocol. Scope approval required before baseline. See reports/architecture_qc_report.json and architecture_defect_registry.json.
