import { describe, expect, it } from 'vitest';
import { connect, createGraph, exportGraph, importGraph, removeNode } from './graph';
describe('canonical graph editing', () => {
    it('round-trips feedback seeds, scope values, prompts and coordinates', () => {
        const graph = createGraph('roundtrip', 'Round trip', 'installed:tag');
        graph.nodes.push({ id: 'critic', type: 'llm', system_prompt: 'Critique', tools_enabled: true, generation: { temperature: 0.3 }, position: { x: 420, y: 180 } });
        graph.loops = [{ id: 'refine', node_ids: ['think', 'critic'], controller_node_id: 'critic', continue_value: 'again', exit_value: 'done' }];
        const value = connect(graph, { id: 'feedback', source: 'critic', target: 'think', target_port: 'previous', kind: 'feedback', loop_id: 'refine', initial_value: null });
        expect(importGraph(exportGraph(value))).toEqual(value);
        expect(JSON.parse(exportGraph(value))).not.toHaveProperty('token');
    });
    it('rejects unsafe and unrecognized imported fields with generated schema', () => {
        const graph = createGraph('safe', 'Safe', 'model');
        expect(() => importGraph(JSON.stringify({ ...graph, id: '../outside' }))).toThrow();
        expect(() => importGraph(JSON.stringify({ ...graph, token: 'secret' }))).toThrow();
        expect(() => importGraph(JSON.stringify({ ...graph, revision: '1' }))).toThrow();
    });
    it('never silently replaces an occupied port and supports distinct many-to-many ports', () => {
        const graph = createGraph('g', 'Graph', 'model');
        expect(() => connect(graph, { id: 'collision', source: 'input', target: 'think', target_port: 'question', kind: 'forward' })).toThrow(/provider/);
        const value = connect(graph, { id: 'second', source: 'input', target: 'think', target_port: 'context', kind: 'forward' });
        expect(value.edges.filter(e => e.target === 'think')).toHaveLength(2);
        expect(graph.edges).toHaveLength(2);
    });
    it('deleting a node removes its edges and invalidated scopes without leaving dangling feedback', () => {
        const graph = createGraph('g', 'Graph', 'model');
        graph.loops = [{ id: 'loop', node_ids: ['think'], controller_node_id: 'think', continue_value: 'continue', exit_value: 'stop' }];
        graph.edges.push({ id: 'feedback', source: 'think', target: 'think', target_port: 'previous', kind: 'feedback', loop_id: 'loop', initial_value: 'seed' });
        const removed = removeNode(graph, 'think');
        expect(removed.edges).toEqual([]);
        expect(removed.loops).toEqual([]);
    });
});
