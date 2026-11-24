"""Static model linkage audit; independent of XSD validation."""
import json
from xml.dom import minidom
import xml.etree.ElementTree as ET
from process_executor_v4 import ROOT,B,D
def audit():
    processes={}; namespaces={}; prefixes={}; paths={}; decisions=set(); errors=[]; links=[]
    for f in sorted((ROOT/"models/bpmn").glob("*.bpmn")):
        root=ET.parse(f).getroot()
        nsmap=dict((k.split(":",1)[1],v) for k,v in minidom.parse(str(f)).documentElement.attributes.items() if k.startswith("xmlns:"))
        for p in root.findall(B+"process"):
            pid=p.get("id")
            if pid in processes: errors.append("duplicate process "+pid)
            processes[pid]=p
            namespaces[pid]=root.get('targetNamespace')
            prefixes[pid]=nsmap
            paths[pid]=str(f.relative_to(ROOT))
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
            prefix,sep,child=n.get("calledElement","").partition(":")
            if not sep or not child or prefix not in prefixes[pid]:
                errors.append(pid+": unresolved QName "+n.get("calledElement","")); continue
            if child in namespaces and prefixes[pid][prefix]!=namespaces[child]: errors.append(pid+": namespace mismatch "+child)
            links.append([pid,child])
            if child not in processes: errors.append(pid+": missing child "+child)
    registry=json.loads((ROOT/"models/process_registry.json").read_text())
    registered=[s["id"] for s in registry["processes"]]
    if len(set(registered))!=len(registered) or set(registered)!=set(processes): errors.append("registry coverage or duplicate ID")
    for spec in registry["processes"]:
        if spec["id"] not in processes: continue
        p=processes[spec["id"]]
        if spec["bpmn"]!=paths[spec["id"]] or spec["namespace"]!=namespaces[spec["id"]]: errors.append(spec["id"]+": registry path or namespace mismatch")
        if set(spec["decisions"])!={n.get("id") for n in p.findall(B+"businessRuleTask")}: errors.append(spec["id"]+": decision binding mismatch")
        for b in spec["decisions"].values():
            if (b["file"],b["id"]) not in decisions: errors.append("missing decision "+b["id"])
    return dict(status="FAIL" if errors else "PASS",processes=len(processes),decisions=len(decisions),call_links=links,errors=errors)
if __name__=="__main__":
    r=audit(); print(json.dumps(r,indent=2)); raise SystemExit(bool(r["errors"]))
