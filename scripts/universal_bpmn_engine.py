"""Restricted recursive BPMN execution kernel. Simulation inputs, not authority enforcement."""
import json
from hashlib import sha256
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path
from dmn_interpreter import D,evaluate_detail
from budget_policy_v1 import OPERATIONS
B="{http://www.omg.org/spec/BPMN/20100524/MODEL}"
ROOT=Path(__file__).resolve().parents[1]
def execute(process_id,inputs,registry,instance="I1",max_events=1000,max_depth=10,policy_operations=None):
    operations={**OPERATIONS,**(policy_operations or {})}
    specs={s["id"]:s for s in registry["processes"]}
    if len(specs)!=len(registry["processes"]): raise ValueError("duplicate process")
    events=[]
    last_by_path={}
    def digest(path): return sha256((ROOT/path).read_bytes()).hexdigest()
    def emit(path,**record):
        if len(events)>=max_events: raise RuntimeError("event limit")
        event_id=f"{instance}:E{len(events):06d}"
        events.append(dict(global_step=len(events),event_id=event_id,previous_event_id=events[-1]["event_id"] if events else None,previous_local_event_id=last_by_path.get(path),instance_path=path,**deepcopy(record)))
        last_by_path[path]=event_id
    def resolve(mapping,context):
        def value(v):
            if set(v)=={"ref"}: return context[v["ref"]]
            if set(v)=={"literal"}: return deepcopy(v["literal"])
            if set(v)=={"equals"}:
                q=v["equals"]; a=context[q["ref"]]; b=q["literal"]
                return type(a) is type(b) and a==b
            raise ValueError("unsupported binding")
        return {k:value(v) for k,v in mapping.items()}
    def visit(pid,values,path,stack):
        if pid in stack or len(stack)>=max_depth: raise RuntimeError("recursive call or depth limit")
        s=specs[pid]; root=ET.parse(ROOT/s["bpmn"]).getroot()
        p=root.find(B+"process")
        if p is None or p.get("id")!=pid: raise ValueError("process identity")
        nodes={n.get("id"):n for n in p if n.tag!=B+"sequenceFlow"}
        flows=p.findall(B+"sequenceFlow")
        ids=[n.get("id") for n in p]
        if None in ids or len(set(ids))!=len(ids): raise ValueError("invalid IDs")
        allowed={B+x for x in ("startEvent","endEvent","task","businessRuleTask","exclusiveGateway","callActivity")}
        if any(n.tag not in allowed for n in nodes.values()): raise ValueError("unsupported node")
        if any(f.get("sourceRef") not in nodes or f.get("targetRef") not in nodes for f in flows): raise ValueError("dangling flow")
        starts=[k for k,n in nodes.items() if n.tag==B+"startEvent"]
        if len(starts)!=1: raise ValueError("start count")
        calls=s.get("calls",{}); decisions=s.get("decisions",{})
        if set(calls)!={k for k,n in nodes.items() if n.tag==B+"callActivity"}: raise ValueError("call bindings")
        if set(decisions)!={k for k,n in nodes.items() if n.tag==B+"businessRuleTask"}: raise ValueError("decision bindings")
        context=deepcopy(values); current=starts[0]; children=[]; visits={}
        emit(path,event="process_start",process_id=pid,inputs=context,bpmn_sha256=digest(s["bpmn"]),parent_instance_path=path.rsplit("/",2)[0] if stack else None)
        for step in range(s["max_steps"]):
            n=nodes[current]; emit(path,event="node",node_id=current)
            if n.tag==B+"endEvent":
                emit(path,event="process_end",end=current,context=context)
                return dict(instance_id=path,process_id=pid,end=current,context=context,children=children)
            for operation in s.get("before",{}).get(current,[]):
                updates=operations[operation](context)
                context.update(updates)
                emit(path,event="policy",node_id=current,operation=operation,actor_id=context.get("actor"),updates=updates)
            if current in decisions:
                b=decisions[current]; d=ET.parse(ROOT/b["file"]).getroot()
                matches=[x for x in d.findall(D+"decision") if x.get("id")==b["id"]]
                if len(matches)!=1: raise ValueError("decision identity")
                detail=evaluate_detail(matches[0].find(D+"decisionTable"),context)
                context[b["output"]]=detail["outcome"]
                emit(path,event="decision",node_id=current,decision_id=b["id"],dmn_sha256=digest(b["file"]),actor_id=context.get("actor"),**detail)
            if current in calls:
                b=calls[current]; target=b["process"]
                if n.get("calledElement")!="lpr:"+target or specs[target]["namespace"]!=s["namespace"]: raise ValueError("call target mismatch")
                visits[current]=visits.get(current,0)+1
                cid=path+"/"+current+"/"+str(visits[current])
                emit(path,event="call_start",node_id=current,child_id=cid)
                child=visit(target,resolve(b["inputs"],context),cid,stack+[pid])
                children.append(child)
                context.update(resolve(b["outputs"],{**child["context"],"end":child["end"]}))
                emit(path,event="call_end",node_id=current,child_id=cid)
            for operation in s.get("after",{}).get(current,[]):
                updates=operations[operation](context)
                context.update(updates)
                emit(path,event="policy",node_id=current,operation=operation,updates=updates)
            context.update(s.get("updates",{}).get(current,{}))
            candidates=[]
            for f in flows:
                if f.get("sourceRef")!=current: continue
                c=f.find(B+"conditionExpression")
                if c is None: candidates.append(f); continue
                key,sep,val=c.text.partition(" = ")
                if not sep or key not in context: raise ValueError("unsupported condition")
                expected=json.loads(val)
                if type(context[key]) is type(expected) and context[key]==expected: candidates.append(f)
            if len(candidates)!=1: raise ValueError("nonunique transition")
            f=candidates[0]; emit(path,event="transition",flow_id=f.get("id"),source=current,target=f.get("targetRef"))
            current=f.get("targetRef")
        raise RuntimeError("step limit")
    result=visit(process_id,inputs,instance,[])
    return dict(result=result,events=events,trace_version="1.0",registry_sha256=sha256(json.dumps(registry,sort_keys=True,separators=(",",":")).encode()).hexdigest())
