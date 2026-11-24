"""Restricted sequential callActivity orchestration; no full BPMN runtime."""
import json
import xml.etree.ElementTree as ET
from organization_decision_audit import simulate,digest
from process_executor_v4 import ROOT,B
MODEL="models/bpmn/corporate_decision.bpmn"
def corporate(instance,technical,budget,actors):
    p=ET.parse(ROOT/MODEL).getroot().find(B+"process")
    nodes={n.get("id"):n for n in p if n.tag!=B+"sequenceFlow"}
    flows=p.findall(B+"sequenceFlow")
    assert len(nodes)+len(flows)==len(p)
    assert all(f.get("sourceRef") in nodes and f.get("targetRef") in nodes for f in flows)
    current=next(k for k,n in nodes.items() if n.tag==B+"startEvent")
    results={}; trace=[]
    for step in range(20):
        n=nodes[current]; trace.append(current)
        if n.tag==B+"endEvent":
            return {"instance_id":instance,"model_sha256":digest(MODEL),"trace":trace,"children":results,"outcome":results["deal_approval"]["end"],"decision":next(r["outcome"] for r in reversed(results["deal_approval"]["records"]) if "decision_id" in r)}
        if n.tag==B+"callActivity":
            child=n.get("calledElement").removeprefix("lpr:")
            if child in results: raise ValueError("duplicate child")
            if child=="technical_expertise": inputs=technical
            elif child=="budget_approval": inputs=budget
            elif child=="deal_approval":
                inputs={"requirementsMet":results["technical_expertise"]["end"]=="positive" and results["budget_approval"]["end"]=="approved","revisionAllowed":False}
            else: raise ValueError("unsupported child")
            results[child]=simulate(child,instance+"/"+current,actors["initiator"],actors[child],inputs)
        elif n.tag!=B+"startEvent": raise ValueError("unsupported node")
        outgoing=[f for f in flows if f.get("sourceRef")==current]
        if len(outgoing)!=1 or outgoing[0].find(B+"conditionExpression") is not None: raise ValueError("unsupported transition")
        current=outgoing[0].get("targetRef")
    raise RuntimeError("step limit")
if __name__=="__main__":
    from itertools import product
    cases=[]
    for tech,funds,limit,authorized in product([False,True],repeat=4):
        args=("C"+str(len(cases)+1),dict(requirementsMet=tech,remediable=False),dict(fundsAvailable=funds,withinLimit=limit),{"initiator":"P4","technical_expertise":"P2","budget_approval":"P3","deal_approval":"P1" if authorized else "P2"})
        result=corporate(*args)
        expected="deny" if not authorized else "approve" if tech and funds and limit else "reject"
        assert result["decision"]==expected and result==corporate(*args)
        cases.append(result)
    print(json.dumps({"status":"PASS","cases":cases},indent=2))
