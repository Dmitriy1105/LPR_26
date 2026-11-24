from io import BytesIO
from bpmn_qname import parse_scoped,resolve_qname
import json
def main():
    root,scopes=parse_scoped(BytesIO(b'<root xmlns:p="urn:a"><child xmlns:p="urn:b" xmlns:q="urn:a"/><sibling/></root>'))
    assert resolve_qname("p:task",scopes[root])==("urn:a","task")
    assert resolve_qname("p:task",scopes[root[0]])==("urn:b","task")
    assert resolve_qname("q:task",scopes[root[0]])==("urn:a","task")
    assert resolve_qname("p:task",scopes[root[1]])==("urn:a","task")
    for value in ("q:task","p:","p:a:b",""):
        try: resolve_qname(value,scopes[root[1]])
        except ValueError: pass
        else: raise AssertionError("invalid QName accepted")
    print(json.dumps(dict(status="PASS",positive=4,negative=4)))
if __name__=="__main__": main()
