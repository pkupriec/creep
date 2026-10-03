import { describe, expect, it } from 'vitest';
import { addConnection, createDiamond, createLoop, decodeGraph, encodeGraph, portsFor, updatePrompt } from './graph';

describe('canonical editor data (no frontend execution)', () => {
  it('keeps many-to-many named providers and full diamond structure', () => {
    const graph = createDiamond();
    expect(portsFor(graph, 's')).toEqual(['alternatives', 'correctness']);
    expect(graph.edges.filter(e => e.source === 'chat')).toHaveLength(2);
    expect(graph.edges.filter(e => e.source === 'reference')).toHaveLength(2);
    expect(portsFor(graph, 'a')).toEqual(['question', 'reference']);
    expect(graph.edges.filter(e => e.target === 'output')).toHaveLength(1);
  });
  it('rejects two providers for the same input while allowing fan-out', () => {
    const graph = createDiamond();
    expect(() => addConnection(graph, 'b', 's', 'correctness')).toThrow('already has a provider');
    expect(addConnection(graph, 'a', 'b', 'peer').edges.at(-1)).toMatchObject({ source: 'a', target: 'b', target_port: 'peer' });
  });
  it('round-trips exact prompts, positions, feedback seeds and loop contract', () => {
    const graph = updatePrompt(createLoop(), 'd', 'Use all inputs.');
    graph.nodes.find(n => n.id === 'd')!.position = { x: -51, y: 23.5 };
    expect(decodeGraph(encodeGraph(graph))).toEqual(graph);
    expect(graph.loops[0]).toEqual({ id: 'refine', node_ids: ['d', 'c'], controller_node_id: 'c', continue_value: 'continue', exit_value: 'stop' });
    expect(graph.edges.find(e => e.kind === 'feedback')).toMatchObject({ loop_id: 'refine', initial_value: 'No previous critique', target_port: 'previous' });
  });
  it('accepts explicit null seed and rejects missing seed, membership or controller', () => {
    const graph = createLoop();
    const feedback = graph.edges.find(e => e.kind === 'feedback')!;
    feedback.initial_value = null;
    expect(decodeGraph(encodeGraph(graph))).toEqual(graph);
    delete feedback.initial_value;
    expect(() => decodeGraph(encodeGraph(graph))).toThrow('seed');
    const invalid = createLoop();
    invalid.loops[0].controller_node_id = 's';
    expect(() => decodeGraph(encodeGraph(invalid))).toThrow('controller');
    const missingMember = createLoop();
    missingMember.loops[0].node_ids = ['c'];
    expect(() => decodeGraph(encodeGraph(missingMember))).toThrow('membership');
  });
  it('rejects malformed JSON, unknown endpoint and unsupported version', () => {
    expect(() => decodeGraph('{')).toThrow();
    const graph = createDiamond();
    graph.edges[0].target = 'missing';
    expect(() => decodeGraph(encodeGraph(graph))).toThrow('endpoint');
    expect(() => decodeGraph('{"schema_version":2}')).toThrow('schema_version');
  });
  it('edits a prompt immutably without changing graph connectivity', () => {
    const graph = createDiamond();
    const next = updatePrompt(graph, 'a', 'Edited expert');
    expect(graph.nodes.find(n => n.id === 'a')!.system_prompt).toBe('Analyze correctness.');
    expect(next.nodes.find(n => n.id === 'a')!.system_prompt).toBe('Edited expert');
    expect(next.edges).toEqual(graph.edges);
  });
});
