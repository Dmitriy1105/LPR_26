"""Validate decision evidence against the actual registered DMN model."""
import json
import xml.etree.ElementTree as ET
from organization_decision_audit import simulate,digest,load
from process_executor_v4 import ROOT,D
from dmn_interpreter import evaluate_detail
def validate(instance):
    registry=load("models/process_registry.json")
    spec=next(s for s in registry["processes"] if s["id"]==instance["process_id"])
    if instance["bpmn_sha256"]!=digest(spec["bpmn"]): raise ValueError("BPMN hash mismatch")
    if instance["organization_sha256"]!=digest("models/organization/organization_profile_v1.json"): raise ValueError("organization hash mismatch")
    records=instance["records"]
    if [r["step"] for r in records]!=list(range(len(records))): raise ValueError("event order")
    count=0
    for r in records:
        if "decision_id" not in r: continue
        b=spec["decisions"][r["node_id"]]
        if r["decision_id"]!=b["id"] or r["decision_model_sha256"]!=digest(b["file"]): raise ValueError("decision identity")
        d=next(d for d in ET.parse(ROOT/b["file"]).getroot().findall(D+"decision") if d.get("id")==b["id"])
        expected=evaluate_detail(d.find(D+"decisionTable"),r["inputs"])
        if any(r[k]!=expected[k] for k in ("rule_id","outcome","inputs")): raise ValueError("decision evidence mismatch")
        count+=1
    if not count: raise ValueError("missing decisions")
    return count
def main():
    from copy import deepcopy
    a=simulate("deal_approval","audit-v2","P4","P1",dict(requirementsMet=False,revisionAllowed=True))
    count=validate(a)
    assert count==2
    rejected=[]
    for field,value in [("rule_id","fake"),("outcome","deny"),("decision_model_sha256","0"*64),("decision_id","fake")]:
        bad=deepcopy(a)
        next(r for r in bad["records"] if "decision_id" in r)[field]=value
        try: validate(bad)
        except ValueError: rejected.append(field)
        else: raise AssertionError(field)
    print(json.dumps(dict(status="PASS",decisions_replayed=count,mutations_rejected=rejected),indent=2))
if __name__=="__main__": main()
