"""Validate against OMG-published schemas; fail closed on retrieval errors."""
import json, hashlib
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urljoin,urlparse
from pathlib import Path
from tempfile import TemporaryDirectory
from lxml import etree
ROOT=Path(__file__).resolve().parents[1]
XS="{http://www.w3.org/2001/XMLSchema}"
def fetch(url,folder,seen):
    if url in seen: return seen[url]
    if urlparse(url).hostname not in {"www.omg.org","omg.org"}: raise ValueError("unexpected schema host")
    try:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/xml,text/xml,*/*'}),timeout=30) as response: data=response.read()
    except HTTPError as e:
        if e.code != 404 or not url.endswith('/DMN13.xsd'): raise RuntimeError(f'{url}: {e}') from e
        alternate='https://www.omg.org/cgi-bin/doc?dtc/19-12-01'
        with urlopen(alternate,timeout=30) as response: data=response.read()
    path=folder/(hashlib.sha256(url.encode()).hexdigest()+".xsd")
    seen[url]=path
    tree=etree.fromstring(data,parser=etree.XMLParser(resolve_entities=False,no_network=True))
    for tag in ("include","import","redefine"):
        for n in tree.findall(XS+tag):
            loc=n.get("schemaLocation")
            if loc:
                try: n.set('schemaLocation',str(fetch(urljoin(url,loc),folder,seen)))
                except Exception as e: raise RuntimeError(f'{url} dependency {loc}: {e}') from e
    path.write_bytes(etree.tostring(tree))
    return path
def main():
    results=[]
    with TemporaryDirectory() as tmp:
        for kind,url in [("bpmn","https://www.omg.org/spec/BPMN/20100501/BPMN20.xsd"),("dmn","https://www.omg.org/spec/DMN/20191111/DMN13.xsd")]:
            try:
                schema=etree.XMLSchema(etree.parse(str(fetch(url,Path(tmp),{}))))
                for f in sorted((ROOT/"models"/kind).glob("*."+kind)):
                    valid=schema.validate(etree.parse(str(f)))
                    results.append(dict(file=str(f.relative_to(ROOT)),valid=valid,errors=[str(e) for e in schema.error_log]))
            except Exception as e: results.append(dict(schema=url,valid=False,error=str(e)))
    print(json.dumps({"status":"PASS" if results and all(r["valid"] for r in results) else "FAIL","results":results},indent=2))
    raise SystemExit(not results or not all(r["valid"] for r in results))
if __name__=="__main__": main()
