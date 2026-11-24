import json
from copy import deepcopy
from organization_engine_v1 import generate
from event_journal_equivalence_v1 import audit_journal_equivalence
def fixtures():
    org=generate(seed=42,count=1)[0]; person=org["people"][1]
    hr=[dict(event_id="HR-1",org_id=org["id"],person_id=person["id"],kind="transfer",effective_date="2026-03-01",new_unit=org["units"][2]["id"],source_ref="hr-order-1")]
    physical=[dict(event_id="EV-1",event_type="org_change",occurred_at="2026-03-01T09:00:00+08:00",recorded_at="2026-03-01T09:05:00+08:00",actor_id=org["people"][0]["id"],subject_id=person["id"],source_ref="hr-order-1",source_event_id="HR-1",event_payload=dict(kind="transfer",person_id=person["id"],effective_date="2026-03-01",source_ref="hr-order-1"))]
    return org,hr,physical
def main():
    org,hr,physical=fixtures()
    good=audit_journal_equivalence(org,hr,physical,[dict(event_ids=["EV-1"])])
    assert good["status"]=="PASS" and good["matched"]==1
    missing=audit_journal_equivalence(org,hr,[],[])
    assert missing["status"]=="FAIL" and missing["missing_physical_events"]==["HR-1"]
    bad=deepcopy(physical); bad[0]["event_payload"]["kind"]="termination"
    assert audit_journal_equivalence(org,hr,bad)["mismatches"]
    orphan=deepcopy(physical); orphan[0]["source_event_id"]="UNKNOWN"
    assert audit_journal_equivalence(org,hr,orphan)["orphaned_physical_events"]==["UNKNOWN"]
    gap=audit_journal_equivalence(org,hr,physical,[dict(event_ids=["NOT-THERE"])])
    assert gap["decision_trace_gaps"]
    duplicate=deepcopy(physical)+deepcopy(physical)
    try: audit_journal_equivalence(org,hr,duplicate)
    except ValueError: pass
    else: raise AssertionError("duplicate source representation accepted")
    print(json.dumps(dict(status="PASS",positive_cases=1,negative_cases=5)))
if __name__=="__main__": main()
