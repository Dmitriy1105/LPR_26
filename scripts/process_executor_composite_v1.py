"""Restricted recursive BPMN/DMN executor with registered callActivity support.

This is a project-specific simulation profile, not full BPMN/FEEL conformance.
Call activities must resolve through process_registry.json; recursion, node types,
transition uniqueness and step counts are bounded.
"""
from __future__ import annotations
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from validate_process_profile import B, D
from dmn_interpreter import evaluate_detail

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {B+x for x in ("startEvent","endEvent","task","businessRuleTask","exclusiveGateway","callActivity")}


def _resolve(binding, context):
    if "ref" in binding:
        key = binding["ref"]
        if key not in context:
            raise ValueError("missing call input reference: " + key)
        return context[key]
    if "literal" in binding:
        return binding["literal"]
    if "equals" in binding:
        expr = binding["equals"]
        key = expr["ref"]
        if key not in context:
            raise ValueError("missing equality reference: " + key)
        return context[key] == expr["literal"]
    raise ValueError("unsupported call binding")


def _load_table(binding):
    root = ET.parse(ROOT / binding["file"]).getroot()
    matches = [d for d in root.findall(D+"decision") if d.get("id") == binding["id"]]
    if len(matches) != 1:
        raise ValueError("decision not found: " + binding["id"])
    return matches[0].find(D+"decisionTable")


def run_composite(spec, inputs, registry, hooks=None, *, max_depth=8, _depth=0):
    if _depth >= max_depth:
        raise RuntimeError("maximum nested process depth exceeded")
    processes = {p["id"]: p for p in registry["processes"]}
    if spec["id"] not in processes:
        raise ValueError("process is not registered: " + spec["id"])
    if processes[spec["id"]]["bpmn"] != spec["bpmn"]:
        raise ValueError("process specification differs from registry")
    hooks = hooks or {}
    root = ET.parse(ROOT / spec["bpmn"]).getroot()
    process = root.find(B+"process")
    if process is None or process.get("id") != spec["id"]:
        raise ValueError("BPMN process identity mismatch")
    nodes = {n.get("id"): n for n in process if n.tag != B+"sequenceFlow"}
    flows = process.findall(B+"sequenceFlow")
    if len(nodes) != len([n for n in process if n.tag != B+"sequenceFlow"]):
        raise ValueError("duplicate BPMN node id")
    if any(n.tag not in ALLOWED for n in nodes.values()):
        raise ValueError("unsupported BPMN node in restricted profile")
    if any(f.get("sourceRef") not in nodes or f.get("targetRef") not in nodes for f in flows):
        raise ValueError("dangling sequence flow")
    starts = [k for k,n in nodes.items() if n.tag == B+"startEvent"]
    if len(starts) != 1:
        raise ValueError("exactly one start event required")

    decisions = spec.get("decisions", {})
    calls = spec.get("calls", {})
    if set(decisions) != {k for k,n in nodes.items() if n.tag == B+"businessRuleTask"}:
        raise ValueError("DMN decision binding mismatch")
    if set(calls) != {k for k,n in nodes.items() if n.tag == B+"callActivity"}:
        raise ValueError("callActivity binding mismatch")
    tables = {k: _load_table(v) for k,v in decisions.items()}
    context = dict(inputs)
    trace = []
    current = starts[0]

    for step in range(spec.get("max_steps", 100)):
        node = nodes[current]
        kind = node.tag.removeprefix(B)
        record = {"step": step, "node_id": current, "type": kind}
        trace.append(record)
        if node.tag == B+"endEvent":
            return {"trace": trace, "context": context, "end": current,
                    "process_id": spec["id"]}

        for hook_name in spec.get("before", {}).get(current, []):
            if hook_name not in hooks:
                raise ValueError("unresolved process hook: " + hook_name)
            update = hooks[hook_name](context)
            if not isinstance(update, dict):
                raise ValueError("process hook must return a mapping")
            context.update(update)
            record.setdefault("hooks", []).append({"name": hook_name, "updates": update})

        if current in tables:
            binding = decisions[current]
            detail = evaluate_detail(tables[current], context)
            context[binding["output"]] = detail["outcome"]
            record.update({"decision_id": binding["id"], **detail})

        if current in calls:
            binding = calls[current]
            child_id = binding["process"]
            child_spec = processes.get(child_id)
            if child_spec is None:
                raise ValueError("called process is not registered: " + child_id)
            called_element = node.get("calledElement", "").split(":")[-1]
            if called_element != child_id:
                raise ValueError("calledElement/registry mismatch at " + current)
            child_inputs = {k: _resolve(v, context) for k,v in binding.get("inputs", {}).items()}
            child_hooks = hooks.get("__process_hooks__", {}).get(child_id, {})
            child = run_composite(child_spec, child_inputs, registry, child_hooks,
                                  max_depth=max_depth, _depth=_depth+1)
            mapped = {}
            for target, source in binding.get("outputs", {}).items():
                ref = source.get("ref")
                if ref == "end":
                    mapped[target] = child["end"]
                elif ref == "outcome":
                    if "outcome" not in child["context"]:
                        raise ValueError("child process has no outcome output")
                    mapped[target] = child["context"]["outcome"]
                elif ref in child["context"]:
                    mapped[target] = child["context"][ref]
                else:
                    raise ValueError("unresolved child output reference: " + str(ref))
            context.update(mapped)
            record.update({"called_process": child_id, "call_inputs": child_inputs,
                           "call_outputs": mapped, "child_trace": child["trace"],
                           "child_terminal": child["end"]})

        context.update(spec.get("updates", {}).get(current, {}))
        candidates = []
        for flow in flows:
            if flow.get("sourceRef") != current:
                continue
            condition = flow.find(B+"conditionExpression")
            if condition is None:
                candidates.append(flow)
                continue
            expression = (condition.text or "").strip()
            key, sep, literal = expression.partition(" = ")
            if not sep or key not in context:
                raise ValueError("unsupported BPMN condition: " + expression)
            if context[key] == json.loads(literal):
                candidates.append(flow)
        if len(candidates) != 1:
            raise ValueError(f"expected exactly one outgoing transition at {current}, got {len(candidates)}")
        record["flow_id"] = candidates[0].get("id")
        current = candidates[0].get("targetRef")
    raise RuntimeError("process step limit exceeded: " + spec["id"])
