import json
from bitrix24_rest_adapter_v1 import parse_page,collect_pages,Bitrix24ContractError
def must_fail(fn):
    try: fn()
    except Bitrix24ContractError: return
    raise AssertionError("invalid payload accepted")
def main():
    p1={"result":{"items":[{"id":1},{"id":2}]},"total":3,"next":2}
    p2={"result":{"items":[{"id":3}]},"total":3}
    result=collect_pages("crm.item.list",[p1,p2])
    assert result["record_count"]==3 and result["complete"] is True
    activity=parse_page("crm.activity.list",{"result":[{"ID":10},{"ID":11}],"total":2})
    assert len(activity.records)==2
    tasks=parse_page("tasks.task.list",{"result":{"tasks":[{"id":20}]},"total":1})
    assert tasks.records[0]["id"]==20
    incomplete=collect_pages("crm.item.list",[p1])
    assert incomplete["complete"] is False and incomplete["next_start"]==2
    must_fail(lambda:parse_page("crm.item.list",{"error":"ACCESS_DENIED","error_description":"denied"}))
    must_fail(lambda:parse_page("crm.item.list",{"result":[{"id":1}]}))
    must_fail(lambda:collect_pages("crm.item.list",[p1,{"result":{"items":[{"id":2}]}}]))
    must_fail(lambda:parse_page("crm.unknown.list",{}))
    must_fail(lambda:parse_page("tasks.task.list",{"result":{"tasks":[{"id":1},None]}}))
    print(json.dumps({"status":"PASS","positive_cases":4,"negative_cases":5}))
if __name__=="__main__":main()
