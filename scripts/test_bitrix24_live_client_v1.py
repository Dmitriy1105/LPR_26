import json
from bitrix24_live_client_v1 import Bitrix24Client,Bitrix24LiveError
def main():
    calls=[]
    def transport(url,body,timeout):
        calls.append((url,body,timeout))
        return 200,json.dumps({"result":{"items":[{"id":1}]},"total":1})
    client=Bitrix24Client("https://example.bitrix24.com","test-secret",transport)
    result=client.call("crm.item.list",{"select[]":["ID","TITLE"]})
    assert result["records"]==[{"id":1}] and result["total"]==1
    assert "test-secret" in calls[0][0] and calls[0][2]==20
    def bad_status(url,body,timeout): return 403,""
    try: Bitrix24Client("https://example.bitrix24.com","x",bad_status).call("crm.item.list")
    except Bitrix24LiveError: pass
    else: raise AssertionError("HTTP error accepted")
    def bad_json(url,body,timeout): return 200,"not-json"
    try: Bitrix24Client("https://example.bitrix24.com","x",bad_json).call("crm.item.list")
    except Bitrix24LiveError: pass
    else: raise AssertionError("invalid JSON accepted")
    for url,token in [("http://example.bitrix24.com","x"),("https://example.bitrix24.com",""),("https://example.bitrix24.com/rest/1/hook","x")]:
        try: Bitrix24Client(url,token,transport)
        except Bitrix24LiveError: pass
        else: raise AssertionError("unsafe configuration accepted")
    try: client.call("user.get")
    except Bitrix24LiveError: pass
    else: raise AssertionError("non-allowlisted method accepted")
    print(json.dumps({"status":"PASS","positive_cases":2,"negative_cases":5,"live_network_used":False}))
if __name__=="__main__":main()
