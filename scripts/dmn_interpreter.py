"""Restricted DMN UNIQUE evaluator, no eval or arbitrary FEEL execution."""
import json,re
from decimal import Decimal
D="{https://www.omg.org/spec/DMN/20191111/MODEL/}"
def literal(s):
    if not isinstance(s,str) or not s.strip(): raise ValueError('missing literal')
    def reject_constant(x): raise ValueError('nonfinite literal '+x)
    v=json.loads(s,parse_float=Decimal,parse_constant=reject_constant)
    if type(v) not in (str,bool,int,Decimal): raise ValueError('unsupported literal')
    return v
def matches(test,value):
    if not isinstance(test,str) or not test.strip(): raise ValueError("missing unary test")
    if test=="-": return True
    m=re.fullmatch(r'([\[(])\s*(.+?)\s*\.\.\s*(.+?)\s*([\])])',test)
    if m:
        a,b=literal(m[2]),literal(m[3])
        if type(value) not in (int,Decimal) or type(a) not in (int,Decimal) or type(b) not in (int,Decimal) or a>b: raise ValueError("invalid interval")
        return (value>=a if m[1]=="[" else value>a) and (value<=b if m[4]=="]" else value<b)
    m=re.fullmatch(r'(<=|>=|<|>)\s*(.+)',test)
    if m:
        a=literal(m[2])
        if type(value) not in (int,Decimal) or type(a) not in (int,Decimal): raise ValueError("invalid comparison")
        return {"<":value<a,">":value>a,"<=":value<=a,">=":value>=a}[m[1]]
    a=literal(test)
    return (type(a)==type(value) or type(a) in (int,Decimal) and type(value) in (int,Decimal)) and a==value
def typed(value,kind):
    if kind=="boolean": ok=type(value) is bool
    elif kind=="string": ok=type(value) is str
    elif kind=="integer": ok=type(value) is int
    elif kind in ("number","decimal"): ok=type(value) in (int,Decimal) and (not isinstance(value,Decimal) or value.is_finite())
    else: raise ValueError("unsupported type "+str(kind))
    if not ok: raise ValueError("invalid input/output type "+kind)
def evaluate_detail(table,values):
    if table is None or table.get("hitPolicy")!="UNIQUE": raise ValueError("unsupported hit policy")
    expr=[i.find(D+"inputExpression") for i in table.findall(D+"input")]
    if any(e is None for e in expr): raise ValueError("missing input expression")
    names=[e.findtext(D+"text") for e in expr]
    if not names or any(not n or not n.strip() for n in names) or len(set(names))!=len(names): raise ValueError("invalid input names")
    snapshot={n:values[n] for n in names}
    for e,n in zip(expr,names): typed(snapshot[n],e.get("typeRef"))
    outputs=table.findall(D+"output")
    if len(outputs)!=1: raise ValueError("single output required")
    found=[]; ids=set()
    for rule in table.findall(D+"rule"):
        rid=rule.get("id")
        if not rid or rid in ids: raise ValueError("invalid rule id")
        ids.add(rid)
        tests=[x.findtext(D+"text") for x in rule.findall(D+"inputEntry")]
        entries=rule.findall(D+"outputEntry")
        if len(tests)!=len(names) or len(entries)!=1: raise ValueError("invalid rule arity")
        checks=[matches(t,snapshot[n]) for t,n in zip(tests,names)]
        result=literal(entries[0].findtext(D+"text"))
        typed(result,outputs[0].get("typeRef"))
        if all(checks): found.append((rid,result))
    if len(found)!=1: raise ValueError("DMN UNIQUE: expected one match, got "+str(len(found)))
    rid,result=found[0]
    return dict(rule_id=rid,outcome=result,inputs=snapshot)
def evaluate(table,values):
    return evaluate_detail(table,values)["outcome"]
