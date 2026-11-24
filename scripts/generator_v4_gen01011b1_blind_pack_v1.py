"""Build a fresh GEN-010.11B.1 blind sample; write blind pack and restricted key separately."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from generator_v4_scenario_engine_v1 import build
from generator_v4_communication_renderer_v1 import render_communications
from generator_v4_human_review_pack_v1 import build_review_pack

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts"/"gen01011b1"
SAMPLE_SEED=20261125

def main():
    world=build()
    communications=render_communications(world["observable_events"],world["organizations"],world["seed"])
    pack,key,audit=build_review_pack(communications,seed=SAMPLE_SEED)
    pack["audit"]="GEN-010.11B.1"
    pack["title"]="Fresh blinded LLM semantic annotation sample"
    pack["sample_id"]="GEN01011B1-SEED-20261125"
    pack["instructions"]["blindness"]="Annotate visible communication only. Never inspect or infer from the restricted answer key."
    key["audit"]="GEN-010.11B.1-RESTRICTED-ANSWER-KEY"
    key["sample_id"]="GEN01011B1-SEED-20261125"
    audit.update({"audit":"GEN-010.11B.1","sample_id":pack["sample_id"],"selection_seed":SAMPLE_SEED,
                  "scenario_seed":world["seed"],"ground_truth_separate":True,
                  "ground_truth_in_blind_pack":False})
    # Strictly constrain model input to reviewer-visible fields; discard prebuilt reviewer slots.
    visible=[]
    for row in pack["records"]:
        visible.append({k:row[k] for k in ("review_id","subject","body")})
    pack["records"]=visible
    blind_dir=OUT/"blind"
    key_dir=OUT/"restricted"
    blind_dir.mkdir(parents=True,exist_ok=True)
    key_dir.mkdir(parents=True,exist_ok=True)
    blind_path=blind_dir/"gen01011b1_blinded_pack.json"
    key_path=key_dir/"gen01011b1_restricted_answer_key.json"
    audit_path=blind_dir/"gen01011b1_pack_audit.json"
    blind_path.write_text(json.dumps(pack,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    key_path.write_text(json.dumps(key,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    checks={
      "sample_size_220":len(visible)==220,
      "unique_review_ids":len({r["review_id"] for r in visible})==220,
      "answer_key_not_in_blind_schema":all(set(r)=={"review_id","subject","body"} for r in visible),
      "channel_shortcut_removed":all("channel" not in r and "record_format" not in r for r in visible),
      "no_ground_truth_fields":not any(any(k in r for k in ("event_type","ground_truth_event_type","source_event_id","organization_id","deal_id","occurred_at")) for r in visible),
      "no_scenario_markers":not any(any(x in r["body"] for x in ("Контекст события:","Область согласования:","unit_approval:")) for r in visible),
      "all_classes_20":all(v["sample"]==20 for v in audit["per_event_class"].values())
    }
    audit["checks"]=checks
    audit["status"]="PASS" if all(checks.values()) else "FAIL"
    audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    manifest={"sample_id":pack["sample_id"],"selection_seed":SAMPLE_SEED,"scenario_seed":world["seed"],
      "record_count":len(visible),"blind_pack_sha256":hashlib.sha256(blind_path.read_bytes()).hexdigest(),
      "answer_key_sha256":hashlib.sha256(key_path.read_bytes()).hexdigest(),
      "answer_key_separate_directory":True,"ground_truth_accessed_by_pack_builder":False,
      "llm_inference_run":False,"status":audit["status"]}
    (blind_dir/"gen01011b1_pack_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"audit":audit,"manifest":manifest},ensure_ascii=False,sort_keys=True))
    if audit["status"]!="PASS": raise SystemExit(1)
if __name__=="__main__": main()
