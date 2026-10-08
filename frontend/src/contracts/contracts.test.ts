/// <reference types="node" />
import Ajv2020 from 'ajv/dist/2020';
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import schema from './schema.json';
import type { ChatCompletionRequest, FeedbackEdge, Graph } from './generated';

const ajv = new Ajv2020({ strict: false, allErrors: true });
const graphValidator = ajv.compile(schema);
const requestValidator = ajv.compile({ ...schema, $ref: '#/$defs/ChatCompletionRequest' });
const authoritativeTrace = JSON.parse(readFileSync(
  new URL('../../../experiments/hermes-traces.json', import.meta.url), 'utf8',
)).authoritative_final_experiment as { client_trace: Array<{ client_request?: unknown }> };
const actualRequests = authoritativeTrace.client_trace.flatMap(
  (entry) => entry.client_request === undefined ? [] : [entry.client_request],
);

describe('Pinned actual Hermes requests', () => {
  it('uses all three authoritative wire requests', () => {
    expect(actualRequests).toHaveLength(3);
  });

  it.each(actualRequests.map((request, index) => ({ request, index })))(
    'accepts request $index without removing tool names or changing history', ({ request }) => {
      const original = JSON.stringify(request);
      expect(requestValidator(request), JSON.stringify(requestValidator.errors)).toBe(true);
      expect(JSON.stringify(request)).toBe(original);
      const typed = request as ChatCompletionRequest;
      for (const message of typed.messages) {
        if (message.role === 'tool') expect(message.name).toBe('read_file');
      }
      expect(requestValidator({ ...typed, reasoning_effort: 'none' })).toBe(false);
    },
  );
});

function graph(): Graph {
  return {
    schema_version: 1, id: 'synthesis', name: 'Synthesis', revision: 1, base_model: 'installed:tag',
    inputs: [{ id: 'chat', required: true }],
    nodes: [
      { id: 'i', type: 'input', input_id: 'chat' },
      { id: 'a', type: 'llm', system_prompt: 'Synthesize', tools_enabled: true, generation: {} },
      { id: 'o', type: 'output' },
    ],
    edges: [
      { id: 'ia', source: 'i', target: 'a', target_port: 'question', kind: 'forward' },
      { id: 'ao', source: 'a', target: 'o', target_port: 'answer', kind: 'forward' },
    ],
    loops: [], output_node_id: 'o',
  };
}

describe('Python-generated contracts', () => {
  it('round-trips discriminated graph data and visual coordinates', () => {
    const value = graph();
    value.nodes[0].position = { x: 10.5, y: -20 };
    expect(graphValidator(value), JSON.stringify(graphValidator.errors)).toBe(true);
    expect(JSON.parse(JSON.stringify(value))).toEqual(value);
  });

  it('requires feedback seed while preserving explicit null', () => {
    const value = graph();
    const feedback: FeedbackEdge = {
      id: 'aa', source: 'a', target: 'a', target_port: 'previous', kind: 'feedback',
      loop_id: 'refine', initial_value: null,
    };
    value.edges.push(feedback);
    value.loops.push({ id: 'refine', node_ids: ['a'], controller_node_id: 'a',
      continue_value: 'again', exit_value: 'done' });
    expect(graphValidator(value)).toBe(true);
    const missing = JSON.parse(JSON.stringify(value));
    delete missing.edges[2].initial_value;
    expect(graphValidator(missing)).toBe(false);
  });

  it('rejects unsafe IDs, schema version, coercion and semantic extras', () => {
    for (const patch of [{ id: '../outside' }, { revision: '1' }, { schema_version: 2 }, { extra: true }]) {
      expect(graphValidator({ ...graph(), ...patch })).toBe(false);
    }
  });

  it('preserves full text/tool history and raw argument/result strings', () => {
    const value: ChatCompletionRequest = {
      model: 'cg/synthesis', stream: true, stream_options: { include_usage: true }, n: 1,
      messages: [
        { role: 'system', content: 'Keep constraints' },
        { role: 'user', content: [{ type: 'text', text: 'Question' }] },
        { role: 'assistant', content: null, tool_calls: [{ id: 'cg_opaque', type: 'function',
          function: { name: 'read', arguments: '{ "path": "é" }' } }] },
        { role: 'tool', tool_call_id: 'cg_opaque', content: 'raw\nresult' },
      ],
      tools: [{ type: 'function', function: { name: 'read', parameters: { type: 'object' } } }],
    };
    expect(requestValidator(value), JSON.stringify(requestValidator.errors)).toBe(true);
    expect(JSON.parse(JSON.stringify(value))).toEqual(value);
    expect(requestValidator({ ...value, reasoning_effort: 'none' })).toBe(false);
    expect(requestValidator({ ...value, n: 2 })).toBe(false);
  });

  it('rejects multimodal input and unbounded generation values', () => {
    expect(requestValidator({ model: 'cg/synthesis', messages: [
      { role: 'user', content: [{ type: 'image_url', image_url: { url: 'x' } }] },
    ] })).toBe(false);
    expect(requestValidator({ model: 'cg/synthesis', messages: [
      { role: 'user', content: 'Question' },
    ], max_tokens: 0 })).toBe(false);
  });
});

// Compile-time guard: generation must never make a seed optional.
// @ts-expect-error initial_value is required even when the intended value is null.
const missingSeed: FeedbackEdge = { id: 'e', source: 'a', target: 'a', target_port: 'old', kind: 'feedback', loop_id: 'loop' };
void missingSeed;
