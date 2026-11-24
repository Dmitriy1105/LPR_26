"""Generate byte-level catalog and check shared model bindings."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def audit():
    paths=sorted(p for p in (ROOT/"models").rglob("*") if p.is_file())
    catalog=[dict(path=str(p.relative_to(ROOT).as_posix()),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in paths]
    def read(p): return json.loads((ROOT/p).read_text())
    universal={p["id"]:p for p in read("models/process_registry_universal_v1.json")["processes"]}
    profile=read("models/organization/authority_execution_profile_v1.json")
    authoritative={p["id"]:p for p in profile["registry"]["processes"]}
    for pid,s in authoritative.items():
        u=universal[pid]
        for k in ("bpmn","namespace","decisions","updates","max_steps"):
            if s.get(k)!=u.get(k): raise ValueError("registry drift: "+pid+" "+k)
        for node,call in s.get("calls",{}).items():
            if call["process"]!=u["calls"][node]["process"] or call["outputs"]!=u["calls"][node]["outputs"]: raise ValueError("call drift")
    return dict(status="PASS",catalog=catalog,bpmn=sum(p.suffix==".bpmn" for p in paths),dmn=sum(p.suffix==".dmn" for p in paths),scope="shared model references and outputs; authority input differences intentional")
if __name__=="__main__": print(json.dumps(audit(),indent=2))
