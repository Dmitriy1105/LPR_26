import json
from copy import deepcopy
from dmn_interpreter import D,evaluate_detail
from test_dmn_interpreter import table
def main():
    base=table("integer",[("-","ok")])
    cases=[]
    def mutate(name,fn):
        t=deepcopy(base); fn(t); cases.append((name,t))
    mutate("missing_expression",lambda t:t.find(D+"input").remove(t.find(".//"+D+"inputExpression")))
    mutate("missing_name",lambda t:setattr(t.find(".//"+D+"inputExpression/"+D+"text"),"text",None))
    mutate("duplicate_input",lambda t:t.append(deepcopy(t.find(D+"input"))))
    mutate("missing_output",lambda t:t.remove(t.find(D+"output")))
    mutate("duplicate_output",lambda t:t.append(deepcopy(t.find(D+"output"))))
    mutate("missing_rule_id",lambda t:t.find(D+"rule").attrib.pop("id"))
    mutate("missing_test",lambda t:setattr(t.find(".//"+D+"inputEntry/"+D+"text"),"text",None))
    mutate("missing_result",lambda t:setattr(t.find(".//"+D+"outputEntry/"+D+"text"),"text",None))
    mutate("wrong_result_type",lambda t:setattr(t.find(".//"+D+"outputEntry/"+D+"text"),"text","true"))
    mutate("unknown_input_type",lambda t:t.find(".//"+D+"inputExpression").set("typeRef","date"))
    mutate("unknown_output_type",lambda t:t.find(D+"output").set("typeRef","date"))
    for literal in ("NaN","Infinity","null","[]","{}"):
        mutate("literal_"+literal,lambda t,v=literal:setattr(t.find(".//"+D+"inputEntry/"+D+"text"),"text",v))
    mutate("empty_rules",lambda t:t.remove(t.find(D+"rule")))
    mutate("extra_output_entry",lambda t:t.find(D+"rule").append(deepcopy(t.find(".//"+D+"outputEntry"))))
    for name,t in cases:
        try: evaluate_detail(t,{"x":1})
        except ValueError: pass
        else: raise AssertionError(name)
    assert evaluate_detail(base,{"x":1})["outcome"]=="ok"
    print(json.dumps(dict(status="PASS",negative_cases=len(cases),positive_cases=1,tests=[n for n,t in cases])))
if __name__=="__main__": main()
