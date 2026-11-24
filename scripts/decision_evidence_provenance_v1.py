"""Validate provenance metadata and coverage of decision evidence references."""
from datetime import datetime
import re
from event_chronology_v1 import validate_events
SOURCE_TYPES=("crm_activity","email","meeting_minutes","approval_record","hr_order","policy","system_log","other")
def _dt(value,name):
    if not isinstance(value,str): raise ValueError(name+" must be ISO-8601")
    try: parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise ValueError("invalid "+name) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None: raise ValueError(name+" requires timezone")
    return parsed
def audit_evidence_provenance(events,evidence_records,required_source_refs=None):
    validate_events(events)
    refs=set(); rows=[]
    for record in evidence_records:
        required=("source_ref","source_type","captured_at","recorded_at","recorded_by","content_sha256")
        if any(k not in record for k in required): raise ValueError("missing evidence provenance field")
        ref=record["source_ref"]
        if not isinstance(ref,str) or not ref.strip() or ref in refs: raise ValueError("empty or duplicate source_ref")
        refs.add(ref)
        if record["source_type"] not in SOURCE_TYPES: raise ValueError("unknown source_type")
        captured=_dt(record["captured_at"],"captured_at"); recorded=_dt(record["recorded_at"],"recorded_at")
        if recorded<captured: raise ValueError("evidence recorded before capture")
        if not isinstance(record["recorded_by"],str) or not record["recorded_by"].strip(): raise ValueError("missing recorded_by")
        digest=record["content_sha256"]
        if not isinstance(digest,str) or not re.fullmatch(r"[0-9a-fA-F]{64}",digest): raise ValueError("invalid SHA-256 digest")
        rows.append({"source_ref":ref,"status":"METADATA_COMPLETE"})
    used={e["source_ref"] for e in events}
    required=set(required_source_refs or used)
    missing=sorted(required-refs)
    unused=sorted(refs-used)
    return {"schema_version":"1.0","status":"PASS" if not missing else "REVIEW_REQUIRED","evidence_records":len(rows),"event_source_refs":len(used),"covered_source_refs":len(required)-len(missing),"missing_source_refs":missing,"unused_evidence_refs":unused,"records":rows,"integrity_scope":"metadata_and_declared_digest_only"}
