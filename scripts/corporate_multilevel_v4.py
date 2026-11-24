"""Versioned integration; preserve original BP-00 regression."""
import json
import xml.etree.ElementTree as ET
from organization_decision_audit import simulate,digest
from budget_escalation_v4 import escalate
from process_executor_v4 import ROOT,B
MODEL="models/bpmn/corporate_decision_multilevel.bpmn"
def run(instance,technical,budget,actors):
    p=ET.parse(ROOT/MODEL).getroot().find(B+"process")
    nodes={n.get("id"):n for n in p if n.tag!=B+"sequenceFlow"}
    flows=p.findall(B+"sequenceFlow")
    current="start"; children={}; trace=[]; events=[]
    def emit(path,record):
        events.append(dict(global_step=len(events),instance_path=path,record=record))
    for _ in range(20):
        n=nodes[current]; trace.append(current); emit(instance,{"node_id":current})
        if n.tag==B+"endEvent":
            return dict(instance_id=instance,trace=trace,children=children,events=events,decision=decision,model_sha256=digest(MODEL))
        if n.tag==B+"callActivity":
            child=n.get("calledElement").removeprefix("lpr:")
            cid=instance+"/"+current
            if child=="technical_expertise":
                r=simulate(child,cid,actors["initiator"],actors[child],technical)
            elif child=="budget_escalation":
                r=escalate(cid,**budget,start=actors["budget_approval"],initiator=actors["initiator"])
            elif child=="deal_approval":
                b=children["budget_escalation"]["outcome"]
                t=children["technical_expertise"]["end"]
                if b in {"unresolved_limit","no_active_grant","blocked"} or t in {"rework","referred"}:
                    decision="pending"; r={"end":"pending","records":[],"reason":{"budget":b,"technical":t}}
                else:
                    r=simulate(child,cid,actors["initiator"],actors[child],dict(requirementsMet=b=="approved" and t=="positive",revisionAllowed=False))
                    decision=next(x["outcome"] for x in reversed(r["records"]) if "decision_id" in x)
            else: raise ValueError("unsupported child")
            children[child]=r
            if child=="budget_escalation":
                for i,a in enumerate(r["attempts"]):
                    emit(cid,{"attempt":i+1,"actor":a["actor"],"limit":a["limit"],"outcome":a["outcome"]})
                    for record in a.get("audit",{}).get("records",[]): emit(cid+"/"+str(i+1),record)
            else:
                for record in r["records"]: emit(cid,record)
                if r["end"]=="pending": emit(cid,{"status":"pending","reason":r["reason"]})
        outgoing=[f for f in flows if f.get("sourceRef")==current]
        if len(outgoing)!=1: raise ValueError("invalid flow")
        current=outgoing[0].get("targetRef")
    raise RuntimeError("step limit")
if __name__=="__main__":
    cases=[]
    for amount,funds,day,tech,rem,actor,expected in [
      (500000,True,"2026-06-01",True,False,"P1","approve"),
      (500001,True,"2026-06-01",True,False,"P1","approve"),
      (5000001,True,"2026-06-01",True,False,"P1","pending"),
      (100,True,"2027-01-01",True,False,"P1","pending"),
      (100,False,"2026-06-01",True,False,"P1","reject"),
      (100,True,"2026-06-01",False,True,"P1","pending"),
      (100,True,"2026-06-01",False,False,"P1","reject"),
      (100,True,"2026-06-01",True,False,"P2","deny")]:
        args=("M"+str(len(cases)+1),dict(requirementsMet=tech,remediable=rem),dict(amount=amount,funds=funds,as_of=day),dict(initiator="P4",technical_expertise="P2",budget_approval="P3",deal_approval=actor))
        r=run(*args)
        assert r["decision"]==expected and r==run(*args)
        assert [e["global_step"] for e in r["events"]]==list(range(len(r["events"])))
        cases.append(r)
    print(json.dumps({"status":"PASS","cases":cases},indent=2))
