"""Versioned integration; preserve original BP-00 regression."""
import json
import xml.etree.ElementTree as ET
from organization_decision_audit import simulate,digest
from budget_escalation_v4 import escalate
from process_executor_v4 import ROOT,B,D
READINESS='models/dmn/corporate_readiness.dmn'
from dmn_interpreter import evaluate_detail
def readiness(values):
    table=ET.parse(ROOT/READINESS).getroot().find(D+'decision').find(D+'decisionTable')
    detail=evaluate_detail(table,values)
    return detail["outcome"],detail["rule_id"]
MODEL="models/bpmn/corporate_decision_multilevel.bpmn"
def run(instance,technical,budget,actors):
    p=ET.parse(ROOT/MODEL).getroot().find(B+"process")
    nodes={n.get("id"):n for n in p if n.tag!=B+"sequenceFlow"}
    flows=p.findall(B+"sequenceFlow")
    current="start"; children={}; trace=[]; events=[]; context={}; decision=None
    def emit(path,record):
        events.append(dict(global_step=len(events),instance_path=path,record=record))
    for _ in range(20):
        n=nodes[current]; trace.append(current); emit(instance,{"node_id":current})
        if n.tag==B+"businessRuleTask":
            inputs=dict(technicalStatus=children["technical_expertise"]["end"],budgetStatus=children["budget_escalation"]["outcome"])
            context["readiness"],rule=readiness(inputs)
            emit(instance,dict(decision_id="corporate_readiness",rule_id=rule,inputs=inputs,outcome=context["readiness"],dmn_sha256=digest(READINESS)))
        if n.tag==B+"endEvent":
            if current=="pending": decision="pending"
            return dict(instance_id=instance,trace=trace,children=children,events=events,decision=decision,model_sha256=digest(MODEL))
        if n.tag==B+"callActivity":
            child=n.get("calledElement").removeprefix("lpr:")
            cid=instance+"/"+current
            if child=="technical_expertise":
                r=simulate(child,cid,actors["initiator"],actors[child],technical)
            elif child=="budget_escalation":
                r=escalate(cid,**budget,start=actors["budget_approval"],initiator=actors["initiator"])
            elif child=="deal_approval":
                r=simulate(child,cid,actors["initiator"],actors[child],dict(requirementsMet=context["readiness"]=="ready",revisionAllowed=False))
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
        outgoing=[]
        for f in flows:
            if f.get("sourceRef")!=current: continue
            condition=f.find(B+"conditionExpression")
            if condition is None: outgoing.append(f)
            else:
                key,sep,value=condition.text.partition(" = ")
                if not sep or key not in context: raise ValueError("invalid condition")
                if context[key]==json.loads(value): outgoing.append(f)
        if len(outgoing)!=1: raise ValueError("invalid flow")
        emit(instance,{"sequence_flow_id":outgoing[0].get("id")})
        current=outgoing[0].get("targetRef")
    raise RuntimeError("step limit")
if __name__=="__main__":
    from itertools import product
    readiness_cases=[]
    for t,b in product(("positive","negative","rework","referred"),("approved","rejected","unresolved_limit","no_active_grant","blocked")):
        expected="pending" if t in {"rework","referred"} or b in {"unresolved_limit","no_active_grant","blocked"} else "ready" if (t,b)==("positive","approved") else "not_ready"
        inputs=dict(technicalStatus=t,budgetStatus=b)
        actual,rule=readiness(inputs)
        assert actual==expected and rule
        readiness_cases.append(dict(inputs=inputs,outcome=actual,rule=rule))
    for inputs in [dict(technicalStatus="unknown",budgetStatus="approved"),dict(technicalStatus="positive",budgetStatus=None),dict(technicalStatus="positive")]:
        try: readiness(inputs)
        except (ValueError,KeyError): pass
        else: raise AssertionError("invalid readiness input accepted")
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
        assert (r["trace"][-1]=="pending")== (expected=="pending")
        assert ("deal_approval" in r["children"]) == (expected!="pending")
        decisions=[e["record"] for e in r["events"] if e["record"].get("decision_id")=="corporate_readiness"]
        assert len(decisions)==1 and decisions[0]["rule_id"] and len(decisions[0]["dmn_sha256"])==64
        assert len([e for e in r["events"] if "sequence_flow_id" in e["record"]])==len(r["trace"])-1
        cases.append(r)
    print(json.dumps({"status":"PASS","cases":cases,"readiness_cases":readiness_cases,"invalid_inputs_rejected":3},indent=2))
