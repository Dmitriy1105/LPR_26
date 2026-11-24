import json
from copy import deepcopy
from historical_replay_v1 import historical_run,replay
def main():
    commits=["454a", "7dbf1310112fbe2b00f1cf85e4b6029eeca854e3"]
    commits[0]="6ac1500727489a1eef56e4e43a0b739bd9c7ce31"
    inputs=dict(actor="P1",initiator="P4",requirementsMet=True,revisionAllowed=False)
    bundles=[historical_run(c,"deal_approval",inputs) for c in commits]
    for b in bundles: assert replay(b)["status"]=="PASS"
    assert bundles[0]["record"]["result"]==bundles[1]["record"]["result"]
    assert bundles[0]["catalog"]!=bundles[1]["catalog"]
    negatives=0
    for change in (lambda b:b.update(commit="main"),lambda b:b["catalog"].clear(),lambda b:b["record"]["events"].pop(),lambda b:b["inputs"].update(actor="P2"),lambda b:b.update(commit=commits[0])):
        b=deepcopy(bundles[1]); change(b)
        try: replay(b)
        except ValueError: negatives+=1
        else: raise AssertionError("modified bundle accepted")
    print(json.dumps(dict(status="PASS",positive_cases=2,negative_cases=negatives,commits=commits)))
if __name__=="__main__": main()
