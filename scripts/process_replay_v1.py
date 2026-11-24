"""Deterministic replay against trusted original inputs and current model versions."""
from authority_execution_v1 import execute_authoritative
def replay(record,process_id,inputs,instance="I1"):
    expected=execute_authoritative(process_id,inputs,instance)
    for key in ("trace_version","registry_sha256","authority_sources","execution_mode"):
        if record.get(key)!=expected[key]: raise ValueError("metadata mismatch: "+key)
    actual=record.get("events")
    if not isinstance(actual,list) or len(actual)!=len(expected["events"]): raise ValueError("event count mismatch")
    import json
    def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)
    for i,(a,b) in enumerate(zip(actual,expected["events"])):
        if canonical(a)!=canonical(b): raise ValueError("event mismatch at "+str(i))
    if canonical(record.get("result"))!=canonical(expected["result"]): raise ValueError("result mismatch")
    if set(record)!=set(expected): raise ValueError("envelope mismatch")
    return dict(status="PASS",events=len(actual),process_id=process_id)
