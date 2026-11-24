"""Restricted BPMN/DMN simulation profile validator. Standard library only.
Not a full BPMN/FEEL implementation or XSD validator."""
import xml.etree.ElementTree as ET
from pathlib import Path
from itertools import product
import json
B="{http://www.omg.org/spec/BPMN/20100524/MODEL}"
D="{https://www.omg.org/spec/DMN/20191111/MODEL/}"
ROOT=Path(__file__).resolve().parents[1]
def load():
    p=ET.parse(ROOT/"models/bpmn/deal_approval.bpmn").getroot().find(B+"process")
    t=ET.parse(ROOT/"models/dmn/approval_outcome.dmn").getroot().find(D+"decision").find(D+"decisionTable")
    return p,t
def evaluate(t, values):
    assert t.attrib["hitPolicy"]=="UNIQUE"
    names=[i.find(D+"inputExpression").findtext(D+"text") for i in t.findall(D+"input")]
    assert all(type(values[n]) is bool for n in names)
    matches=[]
    for r in t.findall(D+"rule"):
        tests=[x.findtext(D+"text") for x in r.findall(D+"inputEntry")]
        assert len(tests)==len(names) and set(tests)<={"-","true","false"}
        if all(a=="-" or (a=="true")==values[n] for a,n in zip(tests,names)):
            matches.append(json.loads(r.find(D+"outputEntry").findtext(D+"text")))
    assert len(matches)==1, ("DMN non-unique or incomplete",values,matches)
    return matches[0]
def execute(p,t,values,bindings,max_steps=100):
    nodes={n.attrib["id"]:n for n in p if n.tag!=B+"sequenceFlow"}
    flows=p.findall(B+"sequenceFlow")
    assert len({n.attrib["id"] for n in p})==len(p)
    assert all(f.attrib["sourceRef"] in nodes and f.attrib["targetRef"] in nodes for f in flows)
    allowed={B+x for x in ("startEvent","endEvent","task","businessRuleTask","exclusiveGateway")}
    assert all(n.tag in allowed for n in nodes.values())
    starts=[k for k,n in nodes.items() if n.tag==B+"startEvent"]
    assert len(starts)==1
    current=starts[0]; trace=[]; context=dict(values)
    for _ in range(max_steps):
        n=nodes[current]; trace.append(current)
        if n.tag==B+"endEvent": return trace,context
        if n.tag==B+"businessRuleTask": context["outcome"]=evaluate(t,context)
        context.update(bindings.get(current,{}))
        candidates=[]
        for f in flows:
            if f.attrib["sourceRef"]!=current: continue
            c=f.find(B+"conditionExpression")
            if c is None: candidates.append(f)
            else:
                key,sep,val=c.text.partition(" = ")
                assert sep and key in context
                if context[key]==json.loads(val): candidates.append(f)
        assert len(candidates)==1, ("ambiguous or missing transition",current)
        current=candidates[0].attrib["targetRef"]
    raise RuntimeError("step limit exceeded")
def main():
    p,t=load()
    cases=[]
    for a,m,r in product([False,True],repeat=3):
        v=dict(authorized=a,requirementsMet=m,revisionAllowed=r)
        expected="deny" if not a else "approve" if m else "revise" if r else "reject"
        assert evaluate(t,v)==expected
        trace,c=execute(p,t,v,{"recheck":{"requirementsMet":True,"revisionAllowed":False}})
        assert trace[-1]==("blocked" if not a else "end")
        assert ("deny" in trace)==(not a)
        assert ("revise" in trace)==(expected=="revise")
        assert ("approve" in trace)==(a and (m or r))
        assert ("reject" in trace)==(a and not m and not r)
        cases.append({"inputs":v,"decision":expected,"trace":trace})
    try: execute(p,t,dict(authorized=True,requirementsMet=False,revisionAllowed=True),{},30)
    except RuntimeError: pass
    else: raise AssertionError("unbounded loop accepted")
    print(json.dumps({"cases":cases,"loop_guard":"PASS","profile":"restricted","xsd_validated":False},indent=2))
if __name__=="__main__": main()
