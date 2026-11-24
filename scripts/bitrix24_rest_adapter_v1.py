"""Offline parser for classic Bitrix24 REST response envelopes; performs no network or credential handling."""
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Page:
    method: str
    records: list[dict]
    total: int | None
    next_start: int | None

class Bitrix24ContractError(ValueError):
    pass

def _integer(value, field):
    if value is None: return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise Bitrix24ContractError("invalid " + field)
    return value

def parse_page(method: str, payload: dict) -> Page:
    if not isinstance(payload, dict):
        raise Bitrix24ContractError("response must be an object")
    if "error" in payload:
        raise Bitrix24ContractError("Bitrix24 API error: " + str(payload.get("error_description") or payload["error"]))
    result = payload.get("result")
    if method == "crm.item.list":
        if not isinstance(result, dict) or not isinstance(result.get("items"), list):
            raise Bitrix24ContractError("crm.item.list requires result.items")
        records = result["items"]
    elif method == "crm.activity.list":
        if not isinstance(result, list):
            raise Bitrix24ContractError("crm.activity.list requires result array")
        records = result
    elif method == "tasks.task.list":
        if not isinstance(result, dict) or not isinstance(result.get("tasks"), list):
            raise Bitrix24ContractError("tasks.task.list requires result.tasks")
        records = result["tasks"]
    else:
        raise Bitrix24ContractError("unsupported Bitrix24 method")
    if any(not isinstance(row, dict) for row in records):
        raise Bitrix24ContractError("records must be objects")
    total = _integer(payload.get("total", result.get("total") if isinstance(result, dict) else None), "total")
    next_start = _integer(payload.get("next"), "next")
    return Page(method, records, total, next_start)

def collect_pages(method: str, payloads: list[dict]) -> dict:
    if not isinstance(payloads, list) or not payloads:
        raise Bitrix24ContractError("at least one page is required")
    pages = [parse_page(method, payload) for payload in payloads]
    if any(page.method != method for page in pages):
        raise Bitrix24ContractError("mixed methods")
    records = [row for page in pages for row in page.records]
    ids = []
    for row in records:
        key = row.get("id", row.get("ID"))
        if key is None:
            raise Bitrix24ContractError("record without id")
        ids.append(str(key))
    if len(ids) != len(set(ids)):
        raise Bitrix24ContractError("duplicate record id across pages")
    totals = {page.total for page in pages if page.total is not None}
    if len(totals) > 1:
        raise Bitrix24ContractError("inconsistent total across pages")
    total = next(iter(totals)) if totals else None
    if total is not None and len(records) > total:
        raise Bitrix24ContractError("received more records than declared total")
    return {"schema_version":"1.0","method":method,"record_count":len(records),"declared_total":total,"complete":total == len(records) if total is not None else all(p.next_start is None for p in pages),"next_start":pages[-1].next_start,"records":records,"source":"bitrix24_classic_rest_response","live_api_called":False}
