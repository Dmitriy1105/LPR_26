"""Evidence-network resilience under key-person removal; graph connectivity is not a staffing recommendation."""
from organizational_influence_v1 import build_influence_graph
def assess_network_resilience(org,events,chains,critical_person_ids=None):
    graph=build_influence_graph(org,events,chains)
    people={p["id"] for p in org.get("people",[])}
    critical=set(critical_person_ids or [])
    unknown=critical-people
    if unknown: raise ValueError("unknown critical person")
    adjacency={p:set() for p in people}
    for edge in graph["edges"]:
        a,b=edge["source"],edge["target"]
        adjacency[a].add(b); adjacency[b].add(a)
    def components(excluded):
        remaining=people-excluded; count=0; largest=0
        while remaining:
            count+=1; stack=[remaining.pop()]; size=0
            while stack:
                node=stack.pop(); size+=1
                found=adjacency[node]&remaining; remaining-=found; stack.extend(found)
            largest=max(largest,size)
        return count,largest
    base_count,base_largest=components(set())
    scenarios=[]
    targets=sorted(critical) if critical else sorted(people)
    for person in targets:
        count,largest=components({person})
        scenarios.append({"removed_person_id":person,"component_count":count,"largest_component_size":largest,"component_count_delta":count-base_count,"largest_component_loss":base_largest-largest})
    return {"schema_version":"1.0","status":graph["status"],"person_count":len(people),"edge_count":graph["edge_count"],"baseline_component_count":base_count,"baseline_largest_component_size":base_largest,"removal_scenarios":scenarios,"method":"undirected_evidence_edge_connectivity_v1","limitations":["Communication graph is treated as undirected for connectivity only; this does not imply equal or reciprocal influence.","Synthetic event coverage cannot establish actual succession readiness or employee substitutability.","No HR recommendation is generated from graph connectivity alone."]}
