import json
from copy import deepcopy
from organization_engine_v1 import generate
from organizational_changes_v1 import validate_events,project_at,append_event
def main():
    org=generate(count=1)[0]; p=org["people"][1]; unit=org["units"][2]["id"]
    ev=[dict(event_id="E1",org_id=org["id"],person_id=p["id"],kind="transfer",effective_date="2026-03-01",new_unit=unit,source_ref="hr-order-1"),dict(event_id="E2",org_id=org["id"],person_id=p["id"],kind="manager_change",effective_date="2026-04-01",new_manager=org["people"][2]["id"],source_ref="hr-order-2"),dict(event_id="E3",org_id=org["id"],person_id=p["id"],kind="position_change",effective_date="2026-05-01",new_position="senior_specialist",source_ref="hr-order-3")]
    assert validate_events(org,ev)
    assert project_at(org,ev,"2026-02-28")[p["id"]]["unit"]==p["unit"]
    assert project_at(org,ev,"2026-03-15")[p["id"]]["unit"]==unit
    assert project_at(org,ev,"2026-04-15")[p["id"]]["manager"]==org["people"][2]["id"]
    assert project_at(org,ev,"2026-05-15")[p["id"]]["position"]=="senior_specialist"
    assert append_event(ev,dict(event_id="E4",org_id=org["id"],person_id=p["id"],kind="termination",effective_date="2026-06-01",source_ref="hr-order-4"))[-1]["event_id"]=="E4"
    negatives=0
    for mutate in (lambda x:x[0].update(org_id="OTHER"),lambda x:x[0].update(person_id="unknown"),lambda x:x[0].update(kind="promotion"),lambda x:x[0].update(source_ref=""),lambda x:x[0].update(effective_date="2026-99-99"),lambda x:x[0].update(new_unit="unknown"),lambda x:x.append(x[0]),lambda x:x.reverse()):
        bad=deepcopy(ev); mutate(bad)
        try: validate_events(org,bad)
        except ValueError: negatives+=1
        else: raise AssertionError("invalid organizational event accepted")
    print(json.dumps(dict(status="PASS",positive_cases=5,negative_cases=negatives)))
if __name__=="__main__": main()
