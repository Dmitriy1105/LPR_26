"""GEN-010.9 renderer QC report; in-memory only."""
import json
from collections import Counter
from generator_v4_scenario_engine_v1 import build
from generator_v4_composite_bpmn_audit_v1 import CONFIG
from generator_v4_communication_renderer_v1 import render_communications, validate_rendered_communications


def audit():
    world = build(config=CONFIG)
    communications = render_communications(world["observable_events"], world["organizations"], world["seed"])
    validation = validate_rendered_communications(world["observable_events"], communications)
    channels = dict(Counter(row["channel"] for row in communications))
    event_types = dict(Counter(row["event_type"] for row in communications))
    missing = sum(bool(row["missing_fields"]) for row in communications)
    return {
        "status": validation["status"],
        "seed": world["seed"],
        "organizations": len(world["organizations"]),
        "deals": len(world["deals"]),
        "observable_events": len(world["observable_events"]),
        "communications": len(communications),
        "unique_source_events": validation["unique_source_events"],
        "channel_counts": channels,
        "event_type_counts": event_types,
        "missingness_preserved_records": missing,
        "speaker_turns_fabricated": sum(row["speaker_contact_id"] is not None for row in communications),
        "validation_errors": validation["errors"],
        "generation_authorized": CONFIG["generation_authorized"],
        "bulk_generation_enabled": CONFIG["bulk_generation_enabled"],
        "scope": "in-memory observable-only communication rendering; no fixture writes"
    }


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(1)
