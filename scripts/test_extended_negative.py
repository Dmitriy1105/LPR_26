import json
from copy import deepcopy
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from budget_policy_v1 import load
from validate_organization_v1 import validate
from authority_execution_v1 import execute_authoritative
import universal_bpmn_engine as engine
def main():
    results=[]
    def reject(name,fn):
        try: fn()
        except (ValueError,KeyError,RuntimeError): results.append(name)
        else: raise AssertionError("accepted: "+name)
    org=load("organization_profile_v1.json"); budget=load("budget_authority_v1.json")
    validate(org,budget)
    for name,mut in [
      ("duplicate person",lambda o,b:o["people"].append(deepcopy(o["people"][0]))),
      ("duplicate role",lambda o,b:o["roles"].append(deepcopy(o["roles"][0]))),
      ("unknown role",lambda o,b:o["people"][0].update(role="missing")),
      ("unknown manager",lambda o,b:o["people"][0].update(manager="missing")),
      ("self manager",lambda o,b:o["people"][0].update(manager=o["people"][0]["id"])),
      ("hierarchy cycle",lambda o,b:o["people"][0].update(manager="P2")),
      ("unknown grant person",lambda o,b:b["grants"][0].update(person="missing")),
      ("unauthorized grant",lambda o,b:b["grants"][0].update(person="P4")),
      ("negative limit",lambda o,b:b["grants"][0].update(limit=-1)),
      ("boolean limit",lambda o,b:b["grants"][0].update(limit=True)),
      ("reversed dates",lambda o,b:b["grants"][0].update(valid_from="2028-01-01")),
      ("overlap",lambda o,b:b["grants"].append(deepcopy(b["grants"][0]))),
      ("currency",lambda o,b:b.update(currency="USD"))]:
        o,b=deepcopy(org),deepcopy(budget); mut(o,b)
        reject(name,lambda:validate(o,b))
    base=dict(actor="P3",initiator="P4",amount=100,as_of="2026-06-01",fundsAvailable=True)
    for k,v in (("amount",0),("amount",-1),("amount",True),("amount",1.5),("as_of","invalid"),("fundsAvailable",1),("actor","missing")):
        reject("input "+k+repr(v),lambda:execute_authoritative("budget_approval",{**base,k:v}))
    with TemporaryDirectory() as tmp:
        root=Path(tmp); f=root/"test.bpmn"
        def run(body,**extra):
            f.write_text('<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:lpr="urn:test" targetNamespace="urn:test"><process id="test">'+body+'</process></definitions>')
            spec=dict(id="test",bpmn="test.bpmn",namespace="urn:test",max_steps=5,decisions={},**extra)
            with patch.object(engine,"ROOT",root): return engine.execute("test",{},{"processes":[spec]})
        start='<startEvent id="s"/>'; end='<endEvent id="e"/>'
        flow='<sequenceFlow id="f" sourceRef="s" targetRef="e"/>'
        reject("duplicate node",lambda:run(start+start+end+flow))
        reject("dangling flow",lambda:run(start+end+flow.replace('targetRef="e"','targetRef="missing"')))
        reject("unsupported node",lambda:run(start+end+'<parallelGateway id="g"/>'+flow))
        reject("missing start",lambda:run(end))
        reject("ambiguous transition",lambda:run(start+end+flow+flow.replace('id="f"','id="f2"')))
        reject("loop limit",lambda:run(start+end+flow.replace('targetRef="e"','targetRef="s"')))
        reject("recursive call",lambda:run(start+end+'<callActivity id="c" calledElement="lpr:test"/>'+flow.replace('targetRef="e"','targetRef="c"'),calls={"c":{"process":"test","inputs":{},"outputs":{}}}))
    print(json.dumps(dict(status="PASS",negative_tests=len(results),cases=results)))
if __name__=="__main__": main()
