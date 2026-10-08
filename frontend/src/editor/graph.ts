import Ajv2020 from 'ajv/dist/2020';
import schema from '../contracts/schema.json';
import type { Edge, Graph, JsonValue } from '../contracts/generated';
const validate = new Ajv2020({ strict: false, allErrors: true }).compile(schema);
/** Check the generated syntax contract; backend validation owns execution topology. */
export function importGraph(text: string): Graph {
    if (new TextEncoder().encode(text).length > 512 * 1024)
        throw new Error('Graph exceeds the size limit.');
    const value: unknown = JSON.parse(text);
    if (!validate(value))
        throw new Error(validate.errors?.map(error => `${error.instancePath || 'graph'} ${error.message}`).join('; ') ?? 'Invalid graph.');
    return value as Graph;
}
export function exportGraph(graph: Graph): string { return JSON.stringify(importGraph(JSON.stringify(graph)), null, 2); }
export function createGraph(id: string, name: string, model: string): Graph {
    return importGraph(JSON.stringify({ schema_version: 1, id, name, revision: 1, base_model: model,
        inputs: [{ id: 'chat', required: true }],
        nodes: [{ id: 'input', type: 'input', input_id: 'chat', position: { x: 0, y: 80 } },
            { id: 'think', type: 'llm', system_prompt: 'Synthesize the supplied inputs.', tools_enabled: false, generation: {}, position: { x: 280, y: 80 } },
            { id: 'output', type: 'output', position: { x: 560, y: 80 } }],
        edges: [{ id: 'question', source: 'input', target: 'think', target_port: 'question', kind: 'forward' },
            { id: 'answer', source: 'think', target: 'output', target_port: 'answer', kind: 'forward' }], loops: [], output_node_id: 'output' }));
}
export function connect(graph: Graph, edge: Edge): Graph {
    if (graph.edges.some(item => item.id !== edge.id && item.target === edge.target && item.target_port === edge.target_port))
        throw new Error('Each input port has exactly one provider. Choose another port.');
    return { ...graph, edges: [...graph.edges.filter(item => item.id !== edge.id), edge] };
}
export function removeNode(graph: Graph, id: string): Graph {
    const removedScopes = graph.loops.filter(loop => loop.node_ids.includes(id)).map(loop => loop.id);
    return { ...graph, nodes: graph.nodes.filter(node => node.id !== id), loops: graph.loops.filter(loop => !removedScopes.includes(loop.id)),
        edges: graph.edges.filter(edge => edge.source !== id && edge.target !== id && !(edge.kind === 'feedback' && removedScopes.includes(edge.loop_id))) };
}
export function parseValue(text: string): JsonValue { return JSON.parse(text) as JsonValue; }
export function nextPort(graph: Graph, nodeId: string): string {
    const ports = new Set(graph.edges.filter(edge => edge.target === nodeId).map(edge => edge.target_port));
    let port = 'input', index = 2;
    while (ports.has(port))
        port = `input${index++}`;
    return port;
}
