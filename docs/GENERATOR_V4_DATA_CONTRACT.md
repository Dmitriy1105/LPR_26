# LPR_26 — Generator v4.0 Data Contract

**Contract version:** 1.0.0  
**Status:** APPROVED PROJECT REQUIREMENTS / IMPLEMENTATION BLOCKED BY OPEN GATES  
**Branch:** `feature/generator-v4-organization-engine`  
**Date:** 2026-11-24  
**Generation authorization:** NOT GRANTED — do not run bulk generation or overwrite fixtures.  
**Purpose:** define the authoritative requirements, schemas, invariants, provenance and release gates for the next synthetic corporate decision-making dataset.

This contract supersedes proposal 0.1 in this file. It approves the target requirements, not the current implementation. A green existing CI run does not certify this contract or authorize generation.

---

## 1. Approved generation profile

| Parameter | Contract value |
|---|---:|
| Generator | v4.0 |
| Random seed | 42 |
| Organizations | 20 |
| Deals per organization | 40 |
| Total deal episodes | 800 |
| Employees per organization | Variable, 30–40 inclusive |
| Scenario profile | Mixed |
| Conflict/revision scenario family | Exactly 25% = 200 deals |
| Observable-data incompleteness | Exactly 10% = 80 deal episodes affected |
| Ground Truth | Complete hidden synthetic truth; never masked in the gold layer |
| Bulk generation | Prohibited until all release gates are approved |

All random choices must derive from the configured seed and stable entity/event keys. Same seed and same contract/code versions must reproduce byte-equivalent logical outputs. Different seeds must change scenario assignments or generated content without breaking invariants.

### 1.1 Mixed scenario allocation

The v4.0 profile uses mutually exclusive primary scenario families. For 800 deals:

| Primary family | Share | Exact count | Minimum semantic characteristics |
|---|---:|---:|---|
| Routine approval | 50% | 400 | Ordinary review and authorized approval |
| Conflict / revision | 25% | 200 | At least one explicit objection or documented disagreement, response/revision path, final outcome |
| Rejected | 15% | 120 | Explicit authorized rejection and closure |
| Multi-level approval | 10% | 80 | At least two organizational units and a multi-step authority/review path |
| **Total** | **100%** | **800** | |

Conflict is a primary family for the exact-count requirement. Do not silently count routine objections, rejected deals or multi-level deals toward the 200 unless the scenario taxonomy is deliberately revised and the exact-count rule is re-approved. The generator must report both primary-family counts and secondary event characteristics.

### 1.2 Employee variability

Each organization must have 30–40 distinct active employee identities, inclusive. Counts must vary across the 20 organizations (not all fixed at one value), be deterministic for seed 42, and be generated from the organization engine. Every employee must have a valid unit, manager/hierarchy relation where applicable, role and time-bounded employment/assignment status. The six-person hard-coded roster in the current scenario engine is not an acceptable v4.0 organization source.

Required organization units: headquarters plus sales, finance, technical, procurement, legal, project office, security and information security. Unit names may be localized in display data, but stable machine codes must remain unchanged. Organizations may differ in reporting lines, staffing, role combinations and decision policies. Do not infer influence from hierarchy alone.

---

## 2. Output layers and separation

The generator must create distinct, versioned layers. Hidden scenario state and Ground Truth must never be included in NLP input or ordinary CRM projections.

1. **World state:** organizations, units, people, roles, employment/assignment periods, competencies, authority grants, delegations, relationships, deals and scenario configuration.
2. **Process/event journal:** ordered causal business events, BPMN process/task references, DMN decisions, actors, targets, timestamps, authority checks and previous-event links.
3. **CRM projection:** Bitrix24-compatible companies, contacts, deals, activities, tasks and associations. Preserve legacy contract fields where applicable; do not mix v4 records into v3.x directories.
4. **Source communication layer:** email headers/body, call transcript turns and meeting attendance/minutes. Distinguish verbatim utterance, reported speech, meeting-minutes author and actual speaker.
5. **Observable NLP input:** only the fields/text that a downstream NLP model is permitted to see, including the controlled missingness described in §7.
6. **Hidden Ground Truth:** complete generated truth, provenance, actor/target/speaker/addressee/executor/decision-maker labels, authority references and evidence spans. Store separately with access boundaries.
7. **NLP predictions:** downstream-only outputs with model/version, candidate, evidence span, confidence, abstention and prediction timestamp. Prediction generation must not read Ground Truth.
8. **Graph projection:** evidence-backed directed relations with type, scope, polarity, time interval, source evidence and confidence; co-participation remains a separate non-influence relation.

Recommended versioned output root: `src/data/generator_v4_0/`. Do not overwrite `bitrix24_contract_v3_2_3`, v3.3.0 fixtures, or accepted NLP artifacts. Exact file layout is finalized in implementation design before any generation.

---

## 3. Canonical entities and required fields

All entities use stable opaque IDs, explicit schema versions and organization scoping. IDs are identifiers, not evidence of a relationship.

### 3.1 Organization and structure

- `organization_id`, `organization_name`, `industry_profile`, `size_band`, `timezone`, `created_at`.
- Units: `unit_id`, `organization_id`, `parent_unit_id`, `unit_code`, `valid_from`, `valid_to`.
- Organization profiles must be heterogeneous but reproducible. Use a declared synthetic business profile; do not imply that a generated company is a real company.

### 3.2 Person, role and competency

- Person: `contact_id`, `organization_id`, `unit_id`, `manager_contact_id`, `employment_status`, `valid_from`, `valid_to`.
- Role assignment: `role_assignment_id`, `contact_id`, `role_code`, `unit_id`, `valid_from`, `valid_to`, `source_ref`.
- Competency: `competency_code`, `level`, `evidence_refs[]`, `valid_from`, `valid_to`, `status`.
- Role, seniority, competence, authority and influence are separate dimensions. Do not infer one from another.

### 3.3 Authority and delegation

- Grant: `grant_id`, `organization_id`, `holder_contact_id`, `permission_code`, `decision_scope`, `amount_limit`, `currency`, `valid_from`, `valid_to`, `source_document_ref`, `status`.
- Delegation: `delegation_id`, `grantor_contact_id`, `delegate_contact_id`, `permission_code`, `scope`, `amount_limit`, `valid_from`, `valid_to`, `source_ref`, `revocation_ref`.
- Every approve/reject/veto/final-decision event must be authorized at the event timestamp, organization, scope and (where applicable) amount. Assignment of a task does not transfer decision authority.
- Negative QC must reject expired, future-dated, revoked, wrong-scope, wrong-organization, over-limit and undelegated decisions.

### 3.4 Deal / scenario instance

- `deal_id`, `organization_id`, `scenario_instance_id`, `scenario_family`, `decision_scope`, `status`, `created_at`, `closed_at`, `seed`.
- Exactly 40 deals per organization and 800 overall.
- Every deal has one deterministic primary scenario family from §1.1 and a complete event/process history or an explicitly modelled incomplete process outcome. No orphan events.

### 3.5 Business event

Required fields:

- `event_id`, `event_schema_version`, `organization_id`, `deal_id`, `process_instance_id`, `bpmn_process_id`, `bpmn_element_id`, `dmn_decision_id` (nullable where not applicable);
- `event_type`, `event_category`, `decision_scope`, `occurred_at`, `sequence_no`, `previous_event_id`;
- `actor_contact_id`, `target_contact_id`, `addressee_contact_ids[]`, `executor_contact_id`, `decision_maker_contact_id` (nullable when not applicable or unknown);
- `decision_outcome`, `authority_grant_refs[]`, `evidence_refs[]`, `provenance_status`.

Events are generated before communication text. Text must not invent a decision or relationship absent from the event/world state.

### 3.6 Communication/activity

Preserve Bitrix24-compatible fields where applicable:

- `ID`, `TYPE_ID`, `CHANNEL`, `SUBJECT`, `DESCRIPTION`, `CREATED`, `AUTHOR_ID`, `RESPONSIBLE_ID`, `OWNER_TYPE_ID`, `OWNER_ID`, `COMMUNICATIONS[]`.
- Add v4 lineage: `activity_id`, `source_event_id`, `deal_id`, `organization_id`, `channel`, `source_document_id`, `source_revision`, `previous_activity_id`, `observable_status`.
- `COMMUNICATIONS[]` is participant association only; it does not establish authorship, speaker identity, action, target, approval or influence.
- Event-to-communication coverage must be explicit and validated. If one event produces multiple messages or no message, encode the cardinality rule rather than assuming one-to-one.

### 3.7 Evidence and source spans

- `evidence_id`, `document_id`, `activity_id`, `segment_id`, `source_type`, `source_revision`, `text_sha256`;
- `start_offset`, `end_offset` as Unicode code-point offsets, half-open `[start,end)`;
- `span_text`, `observed_speaker_ref`, `speaker_resolution_status`, `reported_speech`, `source_timestamp`.
- Offsets must round-trip to the exact source text. Source revision/hash must be stable and verifiable.

---

## 4. Attribution and decision semantics

The following concepts are mandatory and must never be collapsed:

| Concept | Definition |
|---|---|
| Participant | Person associated with the CRM activity or explicitly attending |
| Document author | Person recorded as author/creator of the source document |
| Speaker | Person who actually uttered the statement |
| Actor | Person who performed the described business action |
| Grammatical subject | Entity referred to as the subject of the statement |
| Target | Person/entity affected by or directed toward the action |
| Addressee | Person(s) to whom the communication/action is addressed |
| Executor | Person who carried out an assigned action |
| Decision maker | Person who made the formal decision |
| Authority holder | Person with valid permission at that time and scope |
| Influencer | Person with evidence-backed influence on another actor's decision |

One person may fill multiple roles in one event, but each field must be independently represented. Email sender is not automatically actor; minutes author is not automatically speaker; executor is not automatically decision maker; hierarchy is not proof of influence.

Attribution status vocabulary: `explicit`, `resolved_from_source`, `ambiguous`, `unknown`, `contradicted`, `not_applicable`. Keep the evidence and resolution method for every non-null personal attribution. Unknown is not neutral and must not be silently imputed.

Event taxonomy must cover at least: request_information, report, delegate, complete_task, review, recommend, consult, object, revise, agree, coordinate, approve, reject, veto, authorize, budget_approve, close. Also represent polarity (affirmative/negated), modality (actual/proposed/conditional/hypothetical/reported/uncertain), decision scope and reported-speech status. Distinguish a statement about a decision from the decision event itself.

---

## 5. Communication realism and diversity

- Render channel-appropriate source structures: email sender/recipient/subject/body; call participants and transcript turns; meeting participants, minutes author, reported speakers and action items.
- Generate multi-turn episodes with questions, replies, evidence requests, recommendations, objections, clarifications, revisions and decisions where scenario rules require them.
- Vary arguments, positions, information, style, level of certainty, references to prior messages and department-specific concerns. Do not rely on synonym replacement, IDs, dates or appended tokens to manufacture uniqueness.
- Every substantive assertion in generated text must be supported by the hidden scenario state or explicitly marked as proposal, hypothesis, report or uncertainty.
- Report normalized exact uniqueness after masking identifiers and boilerplate; template/fingerprint frequency; within- and cross-channel similarity; semantic similarity; event-type and class distributions. Jaccard/TF-IDF/embedding metrics are diagnostics, not a substitute for human review.
- Preserve deterministic text rendering for fixed seed and source state.
- Existing contextual renderer is an initial implementation only; its current three-scope/fixed-role assumptions do not yet satisfy the full v4.0 contract.

---

## 6. Observable-data missingness — exact 10%

**Approved interpretation:** exactly 10% of deal episodes (80 of 800) must have at least one deliberately unavailable eligible observation in the CRM/NLP-visible layer.

Rules:
1. Select exactly 80 distinct deals deterministically from seed 42; publish the selection policy and masked-field distribution in the manifest.
2. Apply missingness only to eligible observable attributes, such as optional author/speaker resolution, optional recipient metadata, role/title visibility, source attachment, transcript segment availability or a non-key contextual field.
3. Do not delete primary IDs, organization/deal/event foreign keys, source-event lineage, required timestamps, or structural references needed for integrity checks.
4. Missingness must be explicit: distinguish `unknown`, `not_recorded`, `not_available_in_source`, `redacted_for_benchmark` and `not_applicable`. Do not encode every case as an empty string or conflate unknown with null.
5. The full hidden world state and Ground Truth remain complete and unchanged. Observable projections must not expose masked values through metadata, filenames, IDs, text, ordering or side channels.
6. Report missingness both by affected deal episode (80/800) and by field/type/channel. The 10% requirement is not 10% of all cells and not permission to drop 10% of records.
7. Missingness masks must be deterministic and reproducible. Add leakage tests proving masked values cannot be reconstructed from the NLP input except through legitimate evidence.

---

## 7. BPMN/DMN execution contract

- Scenario event journal is the causal source of truth for generated business events.
- The process executor must produce a trace that can be reconciled with event IDs, process/task IDs, actor assignments, authority checks, DMN outcomes, timestamps, branch decisions and closure.
- Task assignment never grants authority. Every formal decision must pass temporal, organizational, scope and financial authorization.
- Add negative paths for invalid authority, contradictory decisions, rejected branches, missing evidence, delegation expiry, changed organization structure and process interruption.
- Existing BPMN/DMN runtime is a restricted custom execution profile. Do not claim general OMG BPMN/DMN conformance or standalone executable BPMN model files; current audit records limitations and some BPMN definitions are marked non-executable.
- Do not mark integration accepted based only on schema compatibility or independent component tests. Require event-journal/trace semantic equivalence on the same generated episodes.

---

## 8. Legacy compatibility and unresolved baseline discrepancy

The v4.0 dataset is a new, separately versioned synthetic scenario dataset. It must not overwrite or silently redefine v3.2.3/v3.3.0 artifacts.

A repository audit identified a conflict that must be resolved before the release layout is finalized:
- Earlier project checkpoints and the existing draft contract refer to a legacy 767-record baseline.
- The current architecture audit calculates the inspected committed REST manifest as 677 records: 1 company + 30 contacts + 18 deals + 44 invoices + 540 activities + 44 tasks.
- The older 630-activity fixture and later 540-activity manifest are not interchangeable. Their exact refs, branch, manifest and intended regression scope must be reconciled.

Therefore:
1. Do not claim that the legacy fixture has 767 records until a branch/commit/manifest-level recount proves it.
2. Do not force the new v4.0 scenario count to equal the legacy record count.
3. Maintain a separate legacy compatibility regression and a v4.0 scenario manifest.
4. Resolve and document which exact legacy baseline is canonical before any compatibility migration or fixture replacement.

---

## 9. Manifest, reproducibility and release provenance

Every generated release must include a machine-readable manifest with:

- contract/schema versions, generator version, source commit SHA, branch/ref, seed and full config;
- per-entity/per-channel/per-event-type counts;
- primary scenario-family counts and exact conflict count;
- employee count per organization;
- missingness affected-deal IDs in restricted metadata and aggregate distribution in public QC;
- file paths, SHA-256 checksums, generation timestamp and runtime/dependency versions;
- source-event/communication/ground-truth cardinality and validation summaries;
- explicit `synthetic: true`, `generation_status` and data classification;
- no secrets, real personal data or live Bitrix24 credentials.

Same seed + same code + same contract + same runtime dependencies must reproduce the same logical records and checksums, excluding explicitly volatile manifest metadata such as wall-clock generation timestamp.

---

## 10. Acceptance gates

All gates are mandatory; no weighted average can override a failed hard gate.

### Structural and cardinality
- Exactly 20 organizations, 40 deals per organization, 800 deals overall.
- Each organization has 30–40 employees; counts vary across organizations.
- Exactly 400 routine, 200 conflict/revision, 120 rejected and 80 multi-level primary scenarios.
- Exactly 80 deal episodes affected by observable-data missingness.
- Unique IDs, valid references, no orphan entities/events, valid timestamps and chronology.

### Semantic and authority
- Every formal decision is authorized at its timestamp, scope and amount.
- No task-assignment-to-authority leakage.
- Every conflict scenario contains a supported conflict event and a valid subsequent outcome or explicitly modelled unresolved state.
- No unsupported decision, actor, influence or relationship is introduced by text rendering.
- Contradictions, negation, reported speech and ambiguity have explicit labels.

### Ground Truth and leakage
- Complete hidden truth and provenance; observable missingness does not alter gold truth.
- No gold fields, labels, scenario family shortcuts or hidden IDs leak into NLP input.
- Evidence spans and hashes validate; unknown/ambiguous cases remain unknown/ambiguous.
- NLP predictions are stored separately and cannot read gold during inference.

### Text and NLP evaluation
- Diversity metrics are computed after masking identifiers and boilerplate.
- Independent human review of a stratified sample across scenario family, channel, role and missingness status.
- Held-out gold split by organization/deal episode/template family; no random sentence split leakage.
- Report per-class precision, recall, F1, abstention coverage, calibration where validated, and false-attribution rate.
- Synthetic self-consistency is not presented as real-world NLP accuracy.

### Process and reproducibility
- BPMN/DMN trace and event journal semantically reconcile for the same episodes.
- Positive and negative authorization/process tests pass.
- Same-seed deterministic replay passes; alternate seeds produce varied but valid scenarios.
- All QC reports and checksums are attached to the exact release commit.

---

## 11. Implementation plan and dependencies

| Stage | Work package | Exit condition |
|---|---|---|
| GEN-010.1 | Data contract and config schema | Contract fields, cardinalities and validation rules frozen |
| GEN-010.2 | Organization Engine integration | 20 heterogeneous orgs, 30–40 people each, stable hierarchy and units |
| GEN-010.3 | Authority and delegation | Temporal grants, financial limits, delegation and negative tests |
| GEN-010.4 | Scenario expansion | Exact family counts; 800 deals; event chronology and conflict rules |
| GEN-010.5 | Communication engine | Multi-turn, channel-aware, evidence-grounded text; diversity audit |
| GEN-010.6 | Missingness and Ground Truth | Exactly 80 masked deal episodes in observable layer; complete isolated gold |
| GEN-010.7 | BPMN/DMN integration | Same-episode trace equivalence and negative process tests |
| GEN-010.8 | Pre-generation QC | All hard gates pass on small and full-scale dry-run validation |
| Release gate | Explicit user authorization | Only then may bulk generation run |

Do not modify accepted NLP 09–12 artifacts or legacy fixtures as part of these stages unless a separate reviewed change demonstrates the need.

---

## 12. Open implementation blockers (must be closed before generation)

1. **Organization engine integration:** current `organization_engine_v1.py` produces a variable headcount based on 2–5 specialists per eight departments, which can fall outside the required 30–40. The scenario engine still has a fixed six-person role roster. A canonical person/role/manager mapping is required.
2. **Scenario family enforcement:** current scenario engine selects routine/revision/rejected at 40/40/20 and does not implement the approved 50/25/15/10 exact allocation.
3. **Conflict semantics:** current objection/revision path is not yet an exact-count family with independently validated conflict evidence and resolution.
4. **Observable missingness:** no approved 80/800 masking layer or leakage audit is currently implemented.
5. **Ground Truth:** current projection is a synthetic event-derived record, not independent human truth. Extend schema for full attribution/evidence and preserve strict separation from NLP input.
6. **BPMN/DMN:** current restricted profile and dynamic actor mapping limitations remain; same-episode trace equivalence is required.
7. **Legacy baseline:** resolve the 767-versus-677 fixture discrepancy described in §8.
8. **Text quality:** current deterministic templates/context are not yet independently reviewed for semantic realism or dialogue coherence.
9. **Statistical profile:** define and validate organization-level heterogeneity, scope/role balance, communication channel mix, event lengths, cycle durations and cross-organization variation before full generation.

Each blocker requires a focused implementation, tests, evidence report and CI success on the exact commit. Do not close a blocker by documentation-only assertion.

---

## 13. Current approval boundary

**Approved now:** the project requirements and target profile in this contract.

**Not approved now:** code implementation completion, fixture migration, bulk generation, NLP training, model-quality claims or production deployment.

The next authorized engineering action is to implement GEN-010.1–GEN-010.3 and resolve the blockers without generating the 800-deal dataset. Before any bulk generation, publish a pre-generation QC report and request explicit authorization.
