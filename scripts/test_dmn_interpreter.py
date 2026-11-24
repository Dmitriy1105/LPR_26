"""Independent boundary and rejection tests for restricted DMN profile."""
import json
from decimal import Decimal
import xml.etree.ElementTree as ET
from dmn_interpreter import D,evaluate_detail
def table(kind,rules):
    t=ET.Element(D+"decisionTable",hitPolicy="UNIQUE")
    e=ET.SubElement(ET.SubElement(t,D+"input"),D+"inputExpression",typeRef=kind)
    ET.SubElement(e,D+"text").text="x"
    ET.SubElement(t,D+"output",typeRef="string")
    for i,(test,out) in enumerate(rules):
        r=ET.SubElement(t,D+"rule",id="r"+str(i))
        ET.SubElement(ET.SubElement(r,D+"inputEntry"),D+"text").text=test
        ET.SubElement(ET.SubElement(r,D+"outputEntry"),D+"text").text=json.dumps(out)
    return t
def main():
    passed=[]
    def check(name,t,v,out,rid):
        actual=evaluate_detail(t,{"x":v})
        assert actual==dict(outcome=out,rule_id=rid,inputs={"x":v}),name
        passed.append(name)
    def reject(name,t,v):
        try: evaluate_detail(t,v)
        except (ValueError,KeyError): passed.append(name)
        else: raise AssertionError(name)
    t=table("decimal",[("< 0","low"),("[0..1)","middle"),(">= 1","high")])
    for i,(v,out,rid) in enumerate([("-0.0001","low","r0"),("0","middle","r1"),("0.999999999999999999","middle","r1"),("1","high","r2"),("1.0001","high","r2")]):
        check("decimal_"+str(i),t,Decimal(v),out,rid)
    t2=table("integer",[("<= 10","low"),("> 10","high")])
    check("integer_boundary",t2,10,"low","r0")
    check("integer_above",t2,11,"high","r1")
    check("closed_interval",table("integer",[("[1..3]","yes")]),3,"yes","r0")
    check("open_interval",table("integer",[("(1..3]","yes")]),2,"yes","r0")
    check("string",table("string",[('"approved"',"yes")]),"approved","yes","r0")
    check("boolean",table("boolean",[("false","no"),("true","yes")]),False,"no","r0")
    for name,v in [("bool_as_integer",True),("string_as_integer","10"),("null",None),("decimal_as_integer",Decimal("10"))]:
        reject(name,t2,{"x":v})
    reject("missing_input",t2,{})
    reject("nonfinite",t,{"x":Decimal("NaN")})
    reject("overlap",table("integer",[(">= 0","a"),("<= 10","b")]),{"x":5})
    reject("gap",table("integer",[("< 0","a"),("> 0","b")]),{"x":0})
    reject("reversed_interval",table("integer",[("[3..1]","a")]),{"x":2})
    reject("unsupported_expression",table("integer",[("x+1","a")]),{"x":2})
    bad=table("integer",[("-","a")]); bad.set("hitPolicy","FIRST"); reject("unsupported_policy",bad,{"x":2})
    bad=table("integer",[("-","a"),("-","b")]); bad.findall(D+"rule")[1].set("id","r0"); reject("duplicate_rule",bad,{"x":2})
    bad=table("integer",[("-","a")]); bad.find(D+"rule").remove(bad.find(D+"rule").find(D+"inputEntry")); reject("invalid_arity",bad,{"x":2})
    print(json.dumps(dict(status="PASS",count=len(passed),tests=passed),indent=2))
if __name__=="__main__": main()
