"""Replay trusted historical repository revisions in isolated temporary worktrees."""
import hashlib,json,re,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def git(*args):
    return subprocess.check_output(["git","-C",str(ROOT),*args],text=True).strip()
def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)
def historical_run(commit,pid,inputs,instance="I1"):
    if not isinstance(commit,str) or not re.fullmatch("[0-9a-f]{40}",commit): raise ValueError("full commit SHA required")
    if git("rev-parse",commit+"^{commit}")!=commit: raise ValueError("commit mismatch")
    if subprocess.run(["git","-C",str(ROOT),"merge-base","--is-ancestor",commit,"HEAD"]).returncode!=0: raise ValueError("untrusted revision")
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/"revision"
        git("worktree","add","--detach",str(path),commit)
        try:
            catalog={p.relative_to(path).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ("models","scripts") for p in (path/folder).rglob("*") if p.is_file() and p.suffix in (".py",".json",".bpmn",".dmn")}
            code="import json,sys; from authority_execution_v1 import execute_authoritative; x=json.load(sys.stdin); print(json.dumps(execute_authoritative(x['pid'],x['inputs'],x['instance']),allow_nan=False))"
            run=subprocess.run([sys.executable,"-c",code],cwd=path/"scripts",input=canonical(dict(pid=pid,inputs=inputs,instance=instance)),text=True,capture_output=True,check=True,timeout=60)
            return dict(commit=commit,process_id=pid,inputs=inputs,instance=instance,catalog=catalog,python_version=sys.version.split()[0],record=json.loads(run.stdout))
        finally:
            git("worktree","remove","--force",str(path))
def replay(bundle):
    actual=historical_run(bundle["commit"],bundle["process_id"],bundle["inputs"],bundle["instance"])
    if canonical(actual)!=canonical(bundle): raise ValueError("historical replay mismatch")
    return dict(status="PASS",commit=bundle["commit"],events=len(bundle["record"]["events"]))
