"""GEN-010.12.1: disjoint holdout; evaluator-only key and text-only input."""
import hashlib
import json
from pathlib import Path
from generator_v4_scenario_engine_v1 import build
from generator_v4_communication_renderer_v1 import render_communications
from generator_v4_human_review_pack_v1 import build_review_pack, EVENT_TYPES

OUT = Path("artifacts/gen010121")
SEED = 20261126

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    world = build()
    rows = render_communications(world["observable_events"], world["organizations"], world["seed"])
    assert all(r["renderer_version"] == "1.1.0" for r in rows)
    # Previous selection depends on event IDs, classes and organizations, not rendered wording.
    _, old_key, _ = build_review_pack(rows, seed=20261125)
    excluded = {r["source_event_id"] for r in old_key["records"]}
    # Also exclude original human review selection.
    _, earlier_key, _ = build_review_pack(rows, seed=world["seed"])
    excluded.update(r["source_event_id"] for r in earlier_key["records"])
    pack, key, audit = build_review_pack([r for r in rows if r["source_event_id"] not in excluded], seed=SEED)
    assert audit["status"] == "PASS"
    assert len(key["records"]) == 220
    assert len({r["source_event_id"] for r in key["records"]}) == 220
    assert not excluded.intersection(r["source_event_id"] for r in key["records"])
    assert set(audit["per_event_class"]) == set(EVENT_TYPES)
    assert all(v["sample"] == 20 for v in audit["per_event_class"].values())
    sample_id = "GEN010121-SEED-20261126"
    visible = []
    for r in pack["records"]:
        visible.append({k: r[k] for k in ("review_id", "subject", "body")})
    assert len({r["review_id"] for r in visible}) == 220
    assert {r["review_id"] for r in visible} == {r["review_id"] for r in key["records"]}
    # No class balance or selection audit is exposed in the annotation input.
    blind = {"sample_id": sample_id, "records": visible}
    key["sample_id"] = sample_id
    h = write(OUT/"blind/pack.json", blind)
    kh = write(OUT/"restricted/key.json", key)
    write(OUT/"restricted/audit.json", {"status":"PASS", "sample_id":sample_id,
          "renderer_version":"1.1.0", "selection_seed":SEED, "excluded_source_count":len(excluded),
          "source_overlap":0, "record_count":220, "blind_sha256":h, "key_sha256":kh,
          "selection_audit":audit, "llm_inference_run":False,
          "limitation":"Source-event disjointness does not imply template or text disjointness."})
    print("PASS: 220 records; zero reconstructed prior source-event overlap; annotation pending.")

if __name__ == "__main__":
    main()
