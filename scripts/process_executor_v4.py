"""Config-driven restricted BPMN/DMN executor; not full standard conformance."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from validate_process_profile import B,D,evaluate
ROOT=Path(__file__).resolve().parents[1]
def run(spec,inputs):
    p=ET.parse(ROOT/spec["bpmn"]).getroot().find(B+"process")
    if p is None or p.get("id")!=spec["id"]: raise ValueError("process mismatch")
    nodes={n.get("id"):n for n in p if n.tag!=B+"sequenceFlow"}
    flows=p.findall(B+"sequenceFlow")
    if len({n.get("id") for n in p})!=len(p): raise ValueError("duplicate ID")
    allowed={B+x for x in ("startEvent","endEvent","task","businessRuleTask","exclusiveGateway")}
    if any(n.tag not in allowed for n in nodes.values()): raise ValueError("unsupported node")
    if any(f.get("sourceRef") not in nodes or f.get("targetRef") not in nodes for f in flows): raise ValueError("dangling flow")
    starts=[k for k,n in nodes.items() if n.tag==B+"startEvent"]
    if len(starts)!=1: raise ValueError("start count")
    bindings=spec["decisions"]
    if set(bindings)!={k for k,n in nodes.items() if n.tag==B+"businessRuleTask"}: raise ValueError("decision binding mismatch")
    tables={}
    for k,b in bindings.items():
        root=ET.parse(ROOT/b["file"]).getroot()
        matches=[d for d in root.findall(D+"decision") if d.get("id")==b["id"]]
        if len(matches)!=1: raise ValueError("decision not found")
        tables[k]=matches[0].find(D+"decisionTable")
    context=dict(inputs); trace=[]; current=starts[0]
    for step in range(spec["max_steps"]):
        n=nodes[current]; record={"step":step,"node_id":current,"type":n.tag.removeprefix(B)}
        trace.append(record)
        if n.tag==B+"endEvent": return {"trace":trace,"context":context,"end":current}
        if current in tables:
            b=bindings[current]; value=evaluate(tables[current],context)
            context[b["output"]]=value; record["decision_id"]=b["id"]; record["outcome"]=value
        context.update(spec.get("updates",{}).get(current,{}))
        candidates=[]
        for f in flows:
            if f.get("sourceRef")!=current: continue
            c=f.find(B+"conditionExpression")
            if c is None: candidates.append(f); continue
            key,sep,val=c.text.partition(" = ")
            if not sep or key not in context: raise ValueError("unsupported condition")
            if context[key]==json.loads(val): candidates.append(f)
        if len(candidates)!=1: raise ValueError("nonunique transition")
        record["flow_id"]=candidates[0].get("id")
        current=candidates[0].get("targetRef")
    raise RuntimeError("step limit exceeded")
if __name__=="__main__":
    from itertools import product
    registry=json.loads((ROOT/"models/process_registry.json").read_text())
    spec=registry["processes"][0]
    cases=[]
    for a,m,r in product([False,True],repeat=3):
        inputs=dict(authorized=a,requirementsMet=m,revisionAllowed=r)
        result=run(spec,inputs)
        assert result["end"]==("end" if a else "blocked")
        assert result["context"]["outcome"]==("deny" if not a else "approve" if m or r else "reject")
        assert result==run(spec,inputs)
        cases.append({"inputs":inputs,**result})
    print(json.dumps({"cases":cases,"status":"PASS"},indent=2))
