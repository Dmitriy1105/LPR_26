"""OpenAI-compatible LLM adapter for GEN-010.11B.1. No Ground Truth access."""
from __future__ import annotations
import hashlib,json,os,re,sys,time,urllib.request
from pathlib import Path

LABELS={"request_information","delegate","complete_task","review","recommend","object","revise","unit_approval","approve","reject","close","unclear"}
SYSTEM_PROMPT="""You are annotating synthetic CRM communications for a blinded evaluation. Use ONLY the supplied subject, body, channel and format. Do not infer hidden context. Return exactly one JSON object with keys: primary_event_type, confidence, rationale, event_clarity_1_to_5, naturalness_1_to_5, factual_support_1_to_5, unsupported_claims, ambiguity_notes. primary_event_type must be one of: request_information, delegate, complete_task, review, recommend, object, revise, unit_approval, approve, reject, close, unclear. confidence is 0..1. Ratings are integers 1..5. Rationale must cite visible wording. If the text does not support a class, use unclear."""
def call_api(base,key,model,payload,temperature=0):
    url=base.rstrip("/")+"/chat/completions"
    body={"model":model,"temperature":temperature,"response_format":{"type":"json_object"},
          "messages":[{"role":"system","content":SYSTEM_PROMPT},
                      {"role":"user","content":json.dumps(payload,ensure_ascii=False)}]}
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as response:
        data=json.loads(response.read().decode())
    content=data["choices"][0]["message"]["content"]
    return json.loads(content),data.get("model",model)
def main():
    if len(sys.argv)!=3: raise SystemExit("usage: adapter.py BLIND_PACK.json OUTPUT_ANNOTATIONS.json")
    base=os.environ.get("LLM_API_BASE_URL"); key=os.environ.get("LLM_API_KEY"); model=os.environ.get("LLM_MODEL")
    if not all((base,key,model)): raise SystemExit("LLM_API_BASE_URL, LLM_API_KEY and LLM_MODEL are required; no inference was run.")
    path=Path(sys.argv[1]); output=Path(sys.argv[2])
    pack=json.loads(path.read_text(encoding="utf-8"))
    if pack.get("audit")!="GEN-010.11B.1": raise SystemExit("unexpected sample audit")
    records=pack["records"]
    if len(records)!=220 or len({r["review_id"] for r in records})!=220: raise SystemExit("invalid blinded sample")
    results=[]; observed_models=set()
    for index,row in enumerate(records,1):
        annotation,actual_model=call_api(base,key,model,{k:row[k] for k in ("review_id","subject","body")})
        if annotation.get("primary_event_type") not in LABELS: raise ValueError("invalid event label: "+str(annotation.get("primary_event_type")))
        if not 0<=float(annotation.get("confidence",-1))<=1: raise ValueError("invalid confidence")
        for field in ("event_clarity_1_to_5","naturalness_1_to_5","factual_support_1_to_5"):
            if type(annotation.get(field)) is not int or not 1<=annotation[field]<=5: raise ValueError("invalid rating "+field)
        annotation["review_id"]=row["review_id"]
        results.append(annotation); observed_models.add(actual_model)
        print(f"annotated {index}/220",flush=True)
    payload={"audit":"GEN-010.11B.1-LLM-ANNOTATIONS","sample_id":pack["sample_id"],
      "annotator_type":"LLM","ground_truth_accessed":False,"model_requested":model,
      "models_reported_by_api":sorted(observed_models),"prompt_version":"GEN01011B1-PROMPT-v1",
      "temperature":0,"input_pack_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "records":results}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    manifest={"sample_id":pack["sample_id"],"model_requested":model,"models_reported_by_api":sorted(observed_models),
      "prompt_version":"GEN01011B1-PROMPT-v1","temperature":0,"record_count":len(results),
      "annotation_sha256":digest,"ground_truth_accessed":False,"locked":True,
      "created_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    output.with_name("gen01011b1_llm_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False))
if __name__=="__main__": main()
