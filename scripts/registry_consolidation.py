"""Compose authoritative registry from shared definitions and explicit overrides."""
from copy import deepcopy
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def compose(profile,base=None):
    if base is None: base=json.loads((ROOT/"models/process_registry_universal_v1.json").read_text())
    specs={s["id"]:s for s in base["processes"]}
    if len(specs)!=len(base["processes"]): raise ValueError("duplicate process")
    overrides=profile["registry_overrides"]
    if set(overrides)!=set(profile["allowed_inputs"]): raise ValueError("profile coverage")
    result=[]
    for pid,patch in overrides.items():
        if pid not in specs or not set(patch)<= {"before","calls"}: raise ValueError("invalid override")
        s=deepcopy(specs[pid])
        for key,value in patch.items():
            if key=="calls":
                if set(value)!=set(s.get("calls",{})): raise ValueError("call coverage")
                for node,call in value.items():
                    old=s["calls"][node]
                    if call["process"]!=old["process"] or call["outputs"]!=old["outputs"]: raise ValueError("call identity override")
            s[key]=deepcopy(value)
        result.append(s)
    return {"version":base["version"],"processes":result}
