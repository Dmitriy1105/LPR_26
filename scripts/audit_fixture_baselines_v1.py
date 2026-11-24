"""Verify both immutable legacy fixture baselines against actual pages."""
import json
from pathlib import Path
from bitrix24_rest_adapter_v1 import collect_pages
ROOT=Path(__file__).resolve().parents[1]/"src/data"
def audit(root):
    m=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    counts={}
    for spec in m["methods"]:
        pages=[]
        offset=0
        for i,p in enumerate(spec["pages"]):
            assert p["start"]==offset
            data=json.loads((root/p["file"]).read_text(encoding="utf-8"))
            parsed=collect_pages(spec["method"],[data])
            assert parsed["record_count"]==p["count"]
            offset+=p["count"]
            assert data.get("next")== (offset if i+1<len(spec["pages"]) else None)
            pages.append(data)
        result=collect_pages(spec["method"],pages)
        assert result["complete"] and result["record_count"]==spec["recordCount"]
        counts[spec["key"]]=result["record_count"]
    assert counts==m["recordCounts"]
    return {"counts":counts,"total":sum(counts.values()),"version":m.get("datasetVersion",m["snapshotDate"])}
def main():
    old=audit(ROOT/"bitrix24_contract_v1")
    new=audit(ROOT/"bitrix24_contract_v3_2_3")
    assert old["total"]==677 and new["total"]==767
    delta={k:new["counts"][k]-v for k,v in old["counts"].items()}
    assert delta=={k:90 if k=="activities" else 0 for k in delta}
    print(json.dumps({"status":"PASS","legacy":old,"regression":new,"delta":delta,"scope":"legacy_fixture_reconciliation_not_v4_export"}))
if __name__=="__main__": main()
