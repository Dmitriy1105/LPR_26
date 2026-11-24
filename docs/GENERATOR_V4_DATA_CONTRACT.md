# Generator v4.0 — Data Contract proposal 0.1
Status: PROPOSAL_REVIEW_REQUIRED. Synthetic data only. No changes to accepted NLP 09–12 or main.

## Layers
1. World state: organizations, people, departments, time-bounded roles, deal-scoped authority grants, relationships and decision events. Generate causal events before rendering text. Hidden world state is not NLP input.
2. CRM projection: preserve existing Bitrix24 legacy REST fields and 767-record baseline for regression; versioned output root bitrix24_contract_v4_0. COMMUNICATIONS is association, not authorship.
3. Source adapters: email headers and body, call transcript turns, meeting attendance and minutes; explicitly distinguish verbatim from reported speech and unavailable source.
4. Evidence: document_id, activity_id, segment_id, source_type, text, Unicode code-point start/end offsets (half-open), source revision/hash, observed speaker reference and resolution status.
5. Gold events: event_id, evidence_refs, actor_contact_id, target_contact_id, speaker_contact_id, grammatical_subject_ref, relation_type, polarity, modality, decision_scope, occurred_at, attribution_status, annotation_origin. Null allowed; no forced attribution. Separate source observations from hidden synthetic truth.
6. NLP predictions: same event vocabulary, candidate IDs, confidence (uncalibrated until validated), model version, evidence spans, abstention reason. Never read gold during inference.
7. Graph projection: evidence-backed directed edges by scope and time; co-participation separate undirected layer; supplier stance separate from interpersonal relation. No evidence means unknown, not neutral.

## Identity and attribution
Participant = CRM association or explicit attendance; speaker = utterance author; actor = person performing described action; target = person or organization addressed/affected. Email sender is not necessarily actor. Meeting minutes author is not necessarily speaker. A quoted or reported action must preserve reporting source and uncertainty. Distinguish addressee from affected target via addressee_contact_ids and target_contact_id. Include external/internal actor namespace; no fake CRM contact IDs.
Statuses: explicit, resolved_from_source, ambiguous, unknown, contradicted. Only explicit or source-resolved attribution with evidence can qualify as supported in synthetic benchmark; never claim real-world verification.
Example: meeting minutes report “Иванова сообщила, что Петров утвердил бюджет.” Speaker Ivanova, actor Petrov, target null, decision scope budget, reported speech, source minutes. Do not infer that Ivanova approved budget or that Petrov influences Ivanova.

## Event taxonomy proposal
authority: approve, reject, veto, authorize, budget_approve; management: delegate, supervise; influence: recommend, consult, persuade; collaboration: coordinate, agree; opposition: object, block; vendor_stance: support, skeptical, neutral_explicit. Also request_information, report, no_relation. Polarity affirmative/negated; modality actual/proposed/conditional/hypothetical/reported/uncertain (reported speech additionally separate source flag). Separate observed action from durable authority and influence. No automatic edge from request alone.
## Generation
Use channel-specific structures, chronological deal episodes, role/scope-consistent actions, correlated decisions, negative examples, ambiguity and disagreement. Preserve natural text without IDs inserted for uniqueness. Seed and manifest record source SHA, schema version, checksums, scenario family, and generation parameters. Split by organization/deal episode/template family, not random sentences. Keep a separately reviewed gold test set; synthetic labels are not independent validation.
## Acceptance gates (proposed, not measured)
- All references resolve, spans round-trip, timestamps valid, IDs unique, no gold leakage; zero invalid references.
- Every supported personal event has evidence and attribution provenance; unknown cases stay unknown.
- Report normalized uniqueness, masked template counts, TF-IDF and embedding similarity by channel; inspect cross-channel duplicates. Set diversity thresholds only after baseline comparison.
- Report event class and role/scope distributions, ambiguity, negation, chronology, and channel-specific coverage.
- Evaluate actor/target identification and relation classification separately and jointly with precision/recall/F1, per class, abstention coverage and false attribution rate.
- Baseline 30 contacts is insufficient to establish generalization of learned LPR ranking; expand independent synthetic organizations and validate separately before model claims.
