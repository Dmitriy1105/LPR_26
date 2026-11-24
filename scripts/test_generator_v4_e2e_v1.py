import json
from generator_v4_e2e_v1 import audit
def main():
    first=audit(seed=42,count=5); second=audit(seed=42,count=5)
    assert first["status"]=="PASS" and first==second
    assert first["organization_count"]==5
    assert first["entities"]["contacts"]["actual"]==30
    assert first["entities"]["activities"]["actual"]==540
    assert first["entities"]["tasks"]["actual"]==44
    assert all(v for v in first["checks"].values())
    assert first["synthetic"] is True
    assert len(first["limitations"])==4
    print(json.dumps({"status":"PASS","positive_cases":8,"checks":first["total"],"fixture_entities":len(first["entities"])}))
if __name__=="__main__":main()
