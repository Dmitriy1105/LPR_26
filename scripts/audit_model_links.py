"""Static model linkage audit; independent of XSD validation."""
import json
import xml.etree.ElementTree as ET
from process_executor_v4 import ROOT,B,D
def audit():
    processes={}; decisions=set(); errors=[]; links=[]
    for f in sorted((ROOT/"models/bpmn").glob("*.bpmn")):
        for p in ET.parse(f).getroot().findall(B+"process"):
            pid=p.get("id")
            if pid in processes: errors.append("duplicate process "+pid)
            processes[pid]=p
    for f in sorted((ROOT/"models/dmn").glob("*.dmn")):
        for d in ET.parse(f).getroot().findall(D+"decision"): decisions.add((str(f.relative_to(ROOT)),d.get("id")))
    for pid,p in processes.items():
        nodes={n.get("id"):n for n in p if n.tag!=B+"sequenceFlow"}
        flows=p.findall(B+"sequenceFlow")
        ids=[n.get("id") for n in p]
        if None in ids or len(set(ids))!=len(ids): errors.append(pid+": invalid IDs")
        starts=[k for k,n in nodes.items() if n.tag==B+"startEvent"]
        ends={k for k,n in nodes.items() if n.tag==B+"endEvent"}
        if len(starts)!=1 or not ends: errors.append(pid+": invalid endpoints")
        adj={k:set() for k in nodes}
        for f in flows:
            a,b=f.get("sourceRef"),f.get("targetRef")
            if a not in nodes or b not in nodes: errors.append(pid+": dangling flow"); continue
            adj[a].add(b)
        def reach(seed):
            seen=set(); todo=list(seed)
            while todo:
                k=todo.pop()
                if k not in seen: seen.add(k); todo.extend(adj[k]-seen)
            return seen
        if reach(starts)!=set(nodes): errors.append(pid+": unreachable nodes")
        for k in nodes:
            if not reach([k]) & ends: errors.append(pid+": no path to end "+k)
        for n in p.findall(B+"callActivity"):
            child=n.get("calledElement","").split(":")[-1]
            links.append([pid,child])
            if child not in processes: errors.append(pid+": missing child "+child)
    registry=json.loads((ROOT/"models/process_registry.json").read_text())
    for spec in registry["processes"]:
        p=processes[spec["id"]]
        if set(spec["decisions"])!={n.get("id") for n in p.findall(B+"businessRuleTask")}: errors.append(spec["id"]+": decision binding mismatch")
        for b in spec["decisions"].values():
            if (b["file"],b["id"]) not in decisions: errors.append("missing decision "+b["id"])
    return dict(status="FAIL" if errors else "PASS",processes=len(processes),decisions=len(decisions),call_links=links,errors=errors)
if __name__=="__main__":
    r=audit(); print(json.dumps(r,indent=2)); raise SystemExit(bool(r["errors"]))
