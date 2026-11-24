"""Opt-in Bitrix24 REST client. Credentials are read from environment; never log or commit secrets."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from bitrix24_rest_adapter_v1 import parse_page, Bitrix24ContractError

class Bitrix24LiveError(RuntimeError):
    pass

def _base_url(value):
    if not isinstance(value,str) or not value.startswith("https://"):
        raise Bitrix24LiveError("Bitrix24 base URL must use HTTPS")
    if re.search(r"/rest/\d+/[^/]+/?$",value):
        raise Bitrix24LiveError("Pass the REST webhook base path; keep the webhook token in an environment secret")
    return value.rstrip("/")

class Bitrix24Client:
    def __init__(self,base_url=None,webhook_token=None,transport=None):
        self.base_url=_base_url(base_url or os.getenv("BITRIX24_BASE_URL",""))
        self.token=webhook_token or os.getenv("BITRIX24_WEBHOOK_TOKEN","")
        self.user_id=os.getenv("BITRIX24_USER_ID","")
        if not self.token or "/" in self.token or "?" in self.token or not self.user_id.isdigit():
            raise Bitrix24LiveError("Configure BITRIX24_USER_ID and BITRIX24_WEBHOOK_TOKEN as protected environment secrets")
        self.transport=transport or self._https_transport
    @staticmethod
    def _https_transport(url,body,timeout):
        request=urllib.request.Request(url,data=body,headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
        try:
            with urllib.request.urlopen(request,timeout=timeout) as response:
                return response.status,response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code,exc.read().decode("utf-8","replace")
        except urllib.error.URLError as exc:
            raise Bitrix24LiveError("Bitrix24 transport failed") from exc
    def call(self,method,params=None,timeout=20):
        if method not in ("crm.item.list","crm.activity.list","tasks.task.list"):
            raise Bitrix24LiveError("REST method is not allowlisted")
        if not isinstance(timeout,(int,float)) or timeout<=0 or timeout>60:
            raise Bitrix24LiveError("timeout must be between 0 and 60 seconds")
        url=self.base_url+"/rest/"+urllib.parse.quote(self.user_id,safe="")+"/"+urllib.parse.quote(self.token,safe="")+"/"+method+".json"
        body=urllib.parse.urlencode(params or {},doseq=True).encode()
        status,text=self.transport(url,body,timeout)
        if status!=200: raise Bitrix24LiveError("Bitrix24 returned HTTP "+str(status))
        try: payload=json.loads(text)
        except (TypeError,json.JSONDecodeError) as exc: raise Bitrix24LiveError("Bitrix24 returned invalid JSON") from exc
        try: page=parse_page(method,payload)
        except Bitrix24ContractError as exc: raise Bitrix24LiveError(str(exc)) from exc
        return {"method":method,"records":page.records,"total":page.total,"next_start":page.next_start,"http_status":status}
