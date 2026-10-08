"""Compile graph topology without filesystem, provider, or scheduling side effects."""

import heapq
import json

from app.contracts.api import ValidationIssue, ValidationReport
from app.contracts.errors import CGError, ErrorCode
from app.contracts.graph import FeedbackEdge, Graph, InputNode, LLMNode, OutputNode
from app.contracts.interfaces import (
    CompiledGraph,
    GraphSnapshot,
    LoopPlan,
    PortPlan,
    canonical_json,
)


def _reachable(starts: set[str], adjacency: dict[str, set[str]]) -> set[str]:
    seen = set(starts)
    pending = list(starts)
    while pending:
        for successor in adjacency[pending.pop()] - seen:
            seen.add(successor)
            pending.append(successor)
    return seen


def _order(adjacency: dict[str, set[str]]) -> tuple[str, ...]:
    indegree = dict.fromkeys(adjacency, 0)
    for successors in adjacency.values():
        for successor in successors:
            indegree[successor] += 1
    ready = [node for node, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    result = []
    while ready:
        node = heapq.heappop(ready)
        result.append(node)
        for successor in sorted(adjacency[node]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                heapq.heappush(ready, successor)
    return tuple(result)


def _components(adjacency: dict[str, set[str]]) -> list[set[str]]:
    """Iterative Kosaraju avoids a recursion limit for large imported graphs."""
    seen: set[str] = set()
    finished = []
    reverse = {node: set() for node in adjacency}
    for node, successors in adjacency.items():
        for successor in successors:
            reverse[successor].add(node)
    for node in sorted(adjacency):
        stack = [(node, False)]
        while stack:
            current, leaving = stack.pop()
            if leaving:
                finished.append(current)
            elif current not in seen:
                seen.add(current)
                stack.append((current, True))
                stack.extend((n, False) for n in sorted(adjacency[current] - seen))
    seen.clear()
    components = []
    for node in reversed(finished):
        if node not in seen:
            component = set()
            pending = [node]
            while pending:
                current = pending.pop()
                if current not in seen:
                    seen.add(current)
                    component.add(current)
                    pending.extend(reverse[current] - seen)
            components.append(component)
    return components


class GraphValidator:
    """Validate topology and named inputs; coordinates have no execution meaning."""

    def validate(self, graph: Graph) -> ValidationReport:
        errors: list[ValidationIssue] = []

        def issue(code: str, message: str, node: str | None = None, edge: str | None = None):
            errors.append(ValidationIssue(code=code, message=message, node_id=node, edge_id=edge))

        nodes = {node.id: node for node in graph.nodes}
        declared_inputs = {item.id for item in graph.inputs}
        scopes = {member: loop.id for loop in graph.loops for member in loop.node_ids}
        loops = {loop.id: loop for loop in graph.loops}
        forward = {node: set() for node in nodes}
        reverse = {node: set() for node in nodes}
        full = {node: set() for node in nodes}
        ports: set[tuple[str, str]] = set()
        incoming = dict.fromkeys(nodes, 0)
        outputs = [node.id for node in graph.nodes if isinstance(node, OutputNode)]
        if outputs != [graph.output_node_id]:
            issue(
                "output_count",
                "Exactly one configured output node is required.",
                graph.output_node_id,
            )
        inputs = {node.id for node in graph.nodes if isinstance(node, InputNode)}
        if not inputs:
            issue("missing_input", "At least one input node is required.")
        for node in graph.nodes:
            if isinstance(node, InputNode) and node.input_id not in declared_inputs:
                issue("unknown_input", "Input node refers to an undeclared named input.", node.id)
        for edge in graph.edges:
            if edge.source not in nodes or edge.target not in nodes:
                issue("unknown_node", "Edge endpoint does not exist.", edge=edge.id)
                continue
            pair = (edge.target, edge.target_port)
            if pair in ports:
                issue(
                    "duplicate_port",
                    "Each named port must have exactly one provider.",
                    edge.target,
                    edge.id,
                )
            ports.add(pair)
            incoming[edge.target] += 1
            full[edge.source].add(edge.target)
            if isinstance(nodes[edge.target], InputNode):
                issue(
                    "input_has_ports",
                    "Input nodes cannot have inbound edges.",
                    edge.target,
                    edge.id,
                )
            if isinstance(nodes[edge.source], OutputNode):
                issue("output_not_terminal", "Output must be terminal.", edge.source, edge.id)
            if isinstance(edge, FeedbackEdge):
                if edge.loop_id not in loops:
                    issue("unknown_loop", "Feedback requires a declared loop.", edge=edge.id)
                elif (
                    scopes.get(edge.source) != edge.loop_id
                    or scopes.get(edge.target) != edge.loop_id
                ):
                    issue(
                        "feedback_scope",
                        "Feedback endpoints must belong to its loop.",
                        edge=edge.id,
                    )
            else:
                forward[edge.source].add(edge.target)
                reverse[edge.target].add(edge.source)
                source_scope = scopes.get(edge.source)
                if source_scope and scopes.get(edge.target) != source_scope:
                    if edge.source != loops[source_scope].controller_node_id:
                        issue(
                            "loop_output_bypass",
                            "Only a controller may emit outside its scope.",
                            edge.source,
                            edge.id,
                        )
        for node in graph.nodes:
            if isinstance(node, OutputNode) and incoming[node.id] != 1:
                issue("output_ports", "Output must have exactly one input port.", node.id)
            if isinstance(node, LLMNode) and incoming[node.id] == 0:
                issue("missing_ports", "LLM nodes require input data.", node.id)
        order = _order(forward)
        if len(order) != len(nodes):
            issue(
                "forward_cycle",
                "Forward edges must form a DAG.",
                next(node for node in nodes if node not in order),
            )
        reachable = _reachable(inputs, full)
        reversed_full = {node: set() for node in nodes}
        for node, successors in full.items():
            for successor in successors:
                reversed_full[successor].add(node)
        to_output = (
            _reachable({graph.output_node_id}, reversed_full)
            if graph.output_node_id in nodes
            else set()
        )
        for node in nodes:
            if node not in reachable or node not in to_output:
                issue(
                    "unreachable_node",
                    "Every node must be reachable from input and reach output.",
                    node,
                )
        for loop in graph.loops:
            members = set(loop.node_ids)
            if members - nodes.keys():
                issue(
                    "unknown_loop_member",
                    "Loop member does not exist.",
                    sorted(members - nodes.keys())[0],
                )
                continue
            controller = nodes[loop.controller_node_id]
            if not isinstance(controller, LLMNode):
                issue(
                    "invalid_controller",
                    "A controller must be an LLM producing control JSON.",
                    controller.id,
                )
            local = {node: forward[node] & members for node in members}
            local_reverse = {node: reverse[node] & members for node in members}
            if local[controller.id]:
                issue(
                    "controller_not_terminal",
                    "Controller must be final within its scope.",
                    controller.id,
                )
            for node in members - _reachable({controller.id}, local_reverse):
                issue(
                    "controller_unreachable", "Every loop member must reach its controller.", node
                )
            entries = (
                (inputs & members)
                | {
                    edge.target
                    for edge in graph.edges
                    if edge.kind == "forward"
                    and edge.target in members
                    and edge.source not in members
                }
                | {
                    edge.target
                    for edge in graph.edges
                    if isinstance(edge, FeedbackEdge)
                    and edge.loop_id == loop.id
                    and edge.target in members
                }
            )
            for node in members - _reachable(entries, local):
                issue(
                    "scope_unreachable",
                    "Loop members require a forward path from a scope entry.",
                    node,
                )
        for component in _components(full):
            if len(component) > 1 or any(n in full[n] for n in component):
                owners = {scopes.get(n) for n in component}
                if len(owners) != 1 or None in owners:
                    issue(
                        "undeclared_cycle",
                        "Every cyclic component requires one declared scope.",
                        sorted(component)[0],
                    )
        collapsed = {scopes.get(node, f"node:{node}"): set() for node in nodes}
        for node, successors in forward.items():
            source = scopes.get(node, f"node:{node}")
            for successor in successors:
                target = scopes.get(successor, f"node:{successor}")
                if source != target:
                    collapsed[source].add(target)
        if len(_order(collapsed)) != len(collapsed):
            issue("scope_cycle", "Collapsed loop scopes must form a DAG.")
        return ValidationReport(valid=not errors, errors=errors, warnings=[])

    def compile(self, snapshot: GraphSnapshot) -> CompiledGraph:
        graph = snapshot.graph()
        if not self.validate(graph).valid:
            raise CGError(ErrorCode.GRAPH_VALIDATION_FAILED, "Graph topology is invalid.")
        adjacency = {node.id: set() for node in graph.nodes}
        ports = {node.id: [] for node in graph.nodes}
        for edge in graph.edges:
            ports[edge.target].append(edge.target_port)
            if edge.kind == "forward":
                adjacency[edge.source].add(edge.target)
        nodes = {node.id: node for node in graph.nodes}
        final_source = next(
            edge.source for edge in graph.edges if edge.target == graph.output_node_id
        )
        return CompiledGraph(
            snapshot=snapshot,
            forward_order=_order(adjacency),
            ports=tuple(
                PortPlan(node_id=node, ordered_ports=tuple(sorted(ports[node])))
                for node in sorted(nodes)
            ),
            loops=tuple(
                LoopPlan(
                    loop_id=loop.id,
                    members=tuple(sorted(loop.node_ids)),
                    controller_node_id=loop.controller_node_id,
                    inbound_edge_ids=tuple(
                        sorted(
                            e.id
                            for e in graph.edges
                            if e.kind == "forward"
                            and e.target in loop.node_ids
                            and e.source not in loop.node_ids
                        )
                    ),
                    feedback_edge_ids=tuple(
                        sorted(
                            e.id
                            for e in graph.edges
                            if isinstance(e, FeedbackEdge) and e.loop_id == loop.id
                        )
                    ),
                    exit_edge_ids=tuple(
                        sorted(
                            e.id
                            for e in graph.edges
                            if e.kind == "forward"
                            and e.source in loop.node_ids
                            and e.target not in loop.node_ids
                        )
                    ),
                )
                for loop in sorted(graph.loops, key=lambda item: item.id)
            ),
            output_node_id=graph.output_node_id,
            final_llm_node_id=final_source if isinstance(nodes[final_source], LLMNode) else None,
        )

    def prepare_inputs(self, graph: Graph, inputs_json: str) -> str:
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Duplicate input key")
                result[key] = value
            return result

        try:
            values = json.loads(inputs_json, object_pairs_hook=unique_pairs)
            if not isinstance(values, dict):
                raise ValueError("Inputs must be an object")
            declared = {item.id for item in graph.inputs}
            if values.keys() - declared:
                raise ValueError("Unknown input")
            if any(item.required and item.id not in values for item in graph.inputs):
                raise ValueError("Missing required input")
            return canonical_json({item.id: values.get(item.id) for item in graph.inputs})
        except (ValueError, TypeError, RecursionError) as exc:
            raise CGError(ErrorCode.INVALID_PARAMETER, "Invalid or missing named inputs.") from exc
