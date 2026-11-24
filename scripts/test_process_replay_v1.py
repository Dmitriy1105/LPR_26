import json
from copy import deepcopy
from itertools import product
from authority_execution_v1 import execute_authoritative
from process_replay_v1 import replay
def main():
    pid="corporate_multilevel_universal"
    cases=[]
    for amount,funds,day,tech,rem,actor in product((500000,500001,5000001),(False,True),("2026-06-01","2027-01-01"),(False,True),(False,True),("P1","P2")):
        inputs=dict(technicalActor="P2",budgetActor="P3",dealActor=actor,initiator="P4",amount=amount,as_of=day,fundsAvailable=funds,technicalRequirementsMet=tech,remediable=rem)
        r=execute_authoritative(pid,inputs)
        cases.append(replay(r,pid,inputs))
    inputs.update(amount=500001,fundsAvailable=True,as_of="2026-06-01",technicalRequirementsMet=True,dealActor="P1")
    r=execute_authoritative(pid,inputs)
    mutations=[]
    for kind,key,value in [("decision","outcome","tampered"),("decision","rule_id","tampered"),("decision","dmn_sha256","0"*64),("decision","actor_id","P4"),("transition","flow_id","tampered"),("policy","updates",{}),("process_start","bpmn_sha256","0"*64),("call_start","child_id","orphan")]:
        bad=deepcopy(r)
        next(e for e in bad["events"] if e["event"]==kind)[key]=value
        mutations.append(bad)
    for key in ("registry_sha256","authority_sources","result"):
        bad=deepcopy(r); bad[key]={}; mutations.append(bad)
    bad=deepcopy(r); bad["events"].pop(); mutations.append(bad)
    bad=deepcopy(r); bad["events"].append(bad["events"][-1]); mutations.append(bad)
    bad=deepcopy(r); bad["events"][1],bad["events"][2]=bad["events"][2],bad["events"][1]; mutations.append(bad)
    for bad in mutations:
        try: replay(bad,pid,inputs)
        except ValueError: pass
        else: raise AssertionError("mutation accepted")
    print(json.dumps(dict(status="PASS",cases=len(cases),negative_tests=len(mutations),events=sum(c["events"] for c in cases))))
if __name__=="__main__": main()
