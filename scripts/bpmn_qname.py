"""Resolve QName-valued attributes using the element's in-scope namespaces."""
import xml.etree.ElementTree as ET
def parse_scoped(path):
    pending=[]; stack=[]; scopes={}
    parser=ET.iterparse(path,events=("start-ns","start","end"))
    for event,item in parser:
        if event=="start-ns": pending.append(item)
        elif event=="start":
            scope=dict(stack[-1]) if stack else {}
            scope.update(pending); pending.clear()
            stack.append(scope); scopes[item]=scope
        else: stack.pop()
    return parser.root,scopes
def resolve_qname(value,scope):
    if not value or value.count(":")>1: raise ValueError("invalid QName")
    prefix,sep,local=value.partition(":")
    if not sep: prefix,local="",prefix
    if not local or prefix not in scope or not scope[prefix]: raise ValueError("unresolved QName "+value)
    return scope[prefix],local
