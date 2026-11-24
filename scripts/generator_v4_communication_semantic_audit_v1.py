"""GEN-010.10 semantic and attribution audit; Ground Truth is read-only oracle only.

The renderer is never passed Ground Truth. This independent auditor compares rendered
records with observable source events and evaluation-only annotations after rendering.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from generator_v4_communication_renderer_v1 import CHANNELS, ROLE_LABELS, SUBJECTS

CONTEXT_MARKERS = {
    "request_information": ("requirement", "request"),
    "delegate": ("assigned",),
    "complete_task": ("completed",),
    "review": ("review",),
    "recommend": ("recommendation",),
    "object": ("objection",),
    "revise": ("revised",),
    "unit_approval": ("approval",),
    "approve": ("approve",),
    "reject": ("reject",),
    "close": ("deal episode closed",),
}
RECORD_FORMATS = {"email": "email_message", "call": "call_summary", "meeting": "meeting_minutes"}
FORBIDDEN_OUTCOME_TOKENS = ("approved", "rejected", "одобрен", "одобрено", "отклонен", "отклонено")


def audit_rendered_communications(world: dict[str, Any],
                                  communications: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    observable = {row["event_id"]: row for row in world["observable_events"]}
    truth = {row["event_id"]: row for row in world["ground_truth"]["records"]}
    orgs = {row["organization_id"]: row for row in world["organizations"]}
    people = {
        person["contact_id"]: person
        for org in world["organizations"] for person in org["people"]
    }
    roles = {
        org["organization_id"]: {
            assignment["contact_id"]: assignment["role_code"]
            for assignment in org["role_assignments"]
        }
        for org in world["organizations"]
    }
    grants = {row["grant_id"]: row for row in world["authority_grants"]}
    seen: set[str] = set()
    counts = Counter()
    context_present = 0
    context_masked = 0
    author_checks = 0
    executor_checks = 0
    decision_actor_checks = 0
    addressee_checks = 0
    confirming_source_checks = 0
    channel_checks = 0
    role_checks = 0
    semantic_checks = 0
    missingness_checks = 0

    for comm in communications:
        event_id = comm.get("source_event_id")
        if not event_id:
            errors.append("communication missing source_event_id")
            continue
        if event_id in seen:
            errors.append("duplicate communication for " + event_id)
        seen.add(event_id)
        event = observable.get(event_id)
        gold = truth.get(event_id)
        if event is None or gold is None:
            errors.append("orphan observable event or Ground Truth record " + event_id)
            continue

        event_type = event["event_type"]
        counts[event_type] += 1
        organization = orgs.get(event["organization_id"])
        if organization is None:
            errors.append("unknown organization " + event_id)
            continue
        role_map = roles[event["organization_id"]]
        author = event["actor_contact_id"]
        target = event.get("target_contact_id")

        # Author and utterance/document provenance.
        if comm.get("author_contact_id") != author:
            errors.append("author differs from observable actor " + event_id)
        if gold.get("document_author_contact_id") != author:
            errors.append("author differs from evaluation annotation " + event_id)
        if comm.get("author_contact_id") != gold.get("document_author_contact_id"):
            errors.append("rendered author does not reconcile to Ground Truth " + event_id)
        author_checks += 1

        # Executor is event-type dependent. It is not inferred for unrelated event types.
        expected_executor = author if event_type in ("complete_task", "revise") else None
        if event_type in ("complete_task", "revise"):
            if gold.get("executor_contact_id") != expected_executor:
                errors.append("executor annotation mismatch " + event_id)
            if comm.get("action_executor_contact_id") != expected_executor:
                errors.append("rendered action executor mismatch " + event_id)
            executor_checks += 1
        elif comm.get("action_executor_contact_id") is not None:
            errors.append("executor populated for non-execution event " + event_id)
        elif gold.get("executor_contact_id") is not None:
            errors.append("unexpected executor annotation " + event_id)

        # A decision actor is not a decision maker for ordinary events.
        decision_types = ("approve", "reject", "unit_approval")
        expected_decision_actor = author if event_type in decision_types else None
        if gold.get("decision_maker_contact_id") != expected_decision_actor:
            errors.append("decision actor attribution mismatch " + event_id)
        if comm.get("decision_actor_contact_id") != expected_decision_actor:
            errors.append("rendered decision actor mismatch " + event_id)
        if event_type not in decision_types and comm.get("decision_actor_contact_id") is not None:
            errors.append("decision actor populated for non-decision event " + event_id)
        if event_type in decision_types:
            decision_actor_checks += 1
            grant_refs = gold.get("authority_grant_refs", [])
            if not grant_refs:
                errors.append("decision event lacks confirming authority reference " + event_id)
            for grant_id in grant_refs:
                grant = grants.get(grant_id)
                if not grant or grant.get("contact_id") != author:
                    errors.append("decision actor not confirmed by authority grant " + event_id)
                elif grant.get("scope") != event.get("decision_scope"):
                    errors.append("decision scope not confirmed by authority grant " + event_id)

        # Addressee, participants and role labels.
        expected_addressees = [target] if target else []
        expected_participants = [author] + ([target] if target and target != author else [])
        if comm.get("addressee_contact_ids") != expected_addressees:
            errors.append("addressee differs from observable target " + event_id)
        if comm.get("participant_contact_ids") != expected_participants:
            errors.append("participants differ from observable event " + event_id)
        addressee_checks += 1

        author_role = role_map.get(author)
        target_role = role_map.get(target) if target else None
        if comm.get("author_role_code") != author_role:
            errors.append("author role code mismatch " + event_id)
        if comm.get("author_role_label") != ROLE_LABELS.get(author_role, author_role):
            errors.append("author role label mismatch " + event_id)
        expected_target_label = ROLE_LABELS.get(target_role, target_role) if target_role else None
        if comm.get("addressee_role_label") != expected_target_label:
            errors.append("addressee role label mismatch " + event_id)
        role_checks += 1

        # Source chronology and confirming source.
        if comm.get("occurred_at") != event.get("occurred_at"):
            errors.append("communication timestamp differs from source event " + event_id)
        if comm.get("source_ref") != event.get("source_ref") or not event.get("source_ref"):
            errors.append("confirming source reference mismatch " + event_id)
        if comm.get("confirming_source_ref") != event.get("source_ref"):
            errors.append("explicit confirming source lineage mismatch " + event_id)
        if comm.get("deal_id") != event.get("deal_id") or comm.get("organization_id") != event.get("organization_id"):
            errors.append("deal/organization lineage mismatch " + event_id)
        confirming_source_checks += 1

        # Channel and document shape.
        expected_channel, expected_type_id = CHANNELS[event_type]
        if comm.get("channel") != expected_channel or comm.get("type_id") != expected_type_id:
            errors.append("channel mapping mismatch " + event_id)
        if not comm.get("subject") or comm.get("subject") not in SUBJECTS[event_type]:
            errors.append("subject does not belong to event type " + event_id)
        body_lower = comm.get("body", "").lower()
        if comm.get("record_format") != RECORD_FORMATS[expected_channel]:
            errors.append("channel-specific record format mismatch " + event_id)
        channel_checks += 1

        # Observable context is copied verbatim only when it is present.
        note = event.get("context_note")
        if note:
            context_present += 1
            if note not in comm.get("body", ""):
                errors.append("observable context omitted or altered " + event_id)
            if not any(marker in note.lower() for marker in CONTEXT_MARKERS[event_type]):
                errors.append("source context conflicts with event type " + event_id)
        else:
            context_masked += 1
            if comm.get("context_note_included"):
                errors.append("masked context marked as included " + event_id)
            if comm.get("context_note_included") is not False:
                errors.append("missing context inclusion flag not false " + event_id)
        if comm.get("context_note_included") != bool(note):
            errors.append("context inclusion flag mismatch " + event_id)

        # Event semantics and explicit contradictions.
        semantic_terms = {
            "request_information": ("запрос", "исход", "информац", "материал", "сведен"),
            "delegate": ("провер", "поруч", "эксперт", "назнач", "задач"),
            "complete_task": ("заверш", "выполн", "провер", "задач"),
            "review": ("рассмотр", "встреч", "обсужден", "материал", "протокол"),
            "recommend": ("рекомендац", "эксперт", "заключ", "предлага", "оценк"),
            "object": ("возраж", "замечан", "несоглас", "услов", "вопрос"),
            "revise": ("доработ", "коррект", "обнов", "измен", "повторн"),
            "unit_approval": ("согласован", "подраздел", "профильн"),
            "approve": ("одобр", "итогов", "решение", "согласован"),
            "reject": ("отклон", "отказ", "отрицательн"),
            "close": ("закры", "заверш", "эпизод"),
        }
        if not any(term in body_lower for term in semantic_terms[event_type]):
            errors.append("body does not express source event semantics " + event_id)
        if event_type == "approve" and any(term in body_lower for term in ("отклон", "отказ")):
            errors.append("approval communication contains rejection language " + event_id)
        if event_type == "reject" and "одобр" in body_lower:
            errors.append("rejection communication contains approval language " + event_id)
        if event_type == "unit_approval" and any(phrase in body_lower for phrase in ("это итоговое одобрение сделки", "является итоговым одобрением сделки", "подтверждает итоговое одобрение сделки")):
            errors.append("unit approval inflated to final deal approval " + event_id)
        if event_type == "close" and any(term in body_lower for term in FORBIDDEN_OUTCOME_TOKENS):
            errors.append("closure communication exposes final outcome " + event_id)
        if event_type in ("complete_task", "revise"):
            if gold.get("executor_contact_id") != author:
                errors.append("text actor cannot be reconciled to executor " + event_id)
        semantic_checks += 1

        # Missingness is a first-class observable property.
        if comm.get("missing_fields") != event.get("missing_fields"):
            errors.append("missingness metadata mismatch " + event_id)
        if comm.get("speaker_contact_id") is not None or comm.get("speaker_status") != "unknown_no_turn_annotation":
            errors.append("speaker identity invented without turn annotation " + event_id)
        missingness_checks += 1

    expected_ids = set(observable)
    if seen != expected_ids:
        errors.append(f"communication coverage mismatch: missing={len(expected_ids-seen)}, extra={len(seen-expected_ids)}")

    event_counts = dict(sorted(counts.items()))
    return {
        "status": "PASS" if not errors else "FAIL",
        "audit": "GEN-010.10",
        "communications": len(communications),
        "observable_events": len(observable),
        "unique_sources": len(seen),
        "event_type_counts": event_counts,
        "checks": {
            "author_document_provenance": author_checks,
            "executor_event_type_reconciliation": executor_checks,
            "decision_actor_authority_reconciliation": decision_actor_checks,
            "addressee_and_participant_reconciliation": addressee_checks,
            "role_label_reconciliation": role_checks,
            "confirming_source_and_chronology": confirming_source_checks,
            "channel_and_document_format": channel_checks,
            "semantic_event_alignment": semantic_checks,
            "observable_missingness_and_speaker_uncertainty": missingness_checks,
        },
        "context": {
            "visible_context_records": context_present,
            "masked_or_absent_context_records": context_masked,
        },
        "limitations": [
            "Executor, decision actor and confirming source are now explicit fields derived from the observable event; Ground Truth is used only to independently verify them.",
            "Speaker identity remains unknown because turn-level annotations are unavailable.",
            "Automated semantic checks are rule-based; they cannot establish human-level naturalness or full entailment."
        ],
        "warnings": warnings,
        "errors": errors,
    }


if __name__ == "__main__":
    import json
    from generator_v4_scenario_engine_v1 import build
    from generator_v4_communication_renderer_v1 import render_communications
    from generator_v4_composite_bpmn_audit_v1 import CONFIG

    world = build(config=CONFIG)
    communications = render_communications(
        world["observable_events"], world["organizations"], world["seed"]
    )
    report = audit_rendered_communications(world, communications)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(1)
