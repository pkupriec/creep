export type Position = { x: number; y: number };
export type GraphNode = {
  id: string; type: 'input' | 'llm' | 'output'; position: Position;
  input_id?: string; system_prompt?: string; tools_enabled?: boolean;
  generation?: { temperature: number };
};
export type GraphEdge = {
  id: string; source: string; target: string; target_port: string;
  kind: 'forward' | 'feedback'; loop_id?: string; initial_value?: unknown;
};
export type Loop = {
  id: string; node_ids: string[]; controller_node_id: string;
  continue_value: string; exit_value: string;
};
export type Graph = {
  schema_version: 1; id: string; name: string; revision: number; base_model: string;
  inputs: { id: string; required: boolean }[]; nodes: GraphNode[];
  edges: GraphEdge[]; loops: Loop[]; output_node_id: string;
};

const llm = (id: string, x: number, y: number, system_prompt: string): GraphNode => ({
  id, type: 'llm', position: { x, y }, system_prompt, tools_enabled: false,
  generation: { temperature: 0.2 },
});
const edge = (id: string, source: string, target: string, target_port: string): GraphEdge => ({
  id, source, target, target_port, kind: 'forward',
});

export function createDiamond(): Graph {
  return {
    schema_version: 1, id: 'research', name: 'Two experts and synthesis', revision: 1,
    base_model: 'USER_INSTALLED_MODEL',
    inputs: [{ id: 'chat', required: true }, { id: 'reference', required: false }],
    nodes: [
      { id: 'chat', type: 'input', input_id: 'chat', position: { x: 0, y: 10 } },
      { id: 'reference', type: 'input', input_id: 'reference', position: { x: 0, y: 240 } },
      llm('a', 300, 0, 'Analyze correctness.'),
      llm('b', 300, 260, 'Analyze alternatives.'),
      llm('s', 620, 130, 'Synthesize all inputs into the final answer.'),
      { id: 'output', type: 'output', position: { x: 940, y: 130 } },
    ],
    edges: [edge('ia', 'chat', 'a', 'question'), edge('ib', 'chat', 'b', 'question'),
      edge('ra', 'reference', 'a', 'reference'), edge('rb', 'reference', 'b', 'reference'),
      edge('as', 'a', 's', 'correctness'), edge('bs', 'b', 's', 'alternatives'),
      edge('so', 's', 'output', 'answer')],
    loops: [], output_node_id: 'output',
  };
}

export function createLoop(): Graph {
  const graph = createDiamond();
  graph.name = 'Diamond with seeded refinement';
  graph.nodes = graph.nodes.filter(n => n.id !== 'output').concat([
    llm('d', 940, 130, 'Draft an answer using the synthesis and previous critique.'),
    llm('c', 1250, 130, 'Critique draft; return payload and control.decision continue or stop.'),
    { id: 'output', type: 'output', position: { x: 1560, y: 130 } },
  ]);
  graph.edges = graph.edges.filter(e => e.id !== 'so').concat([
    edge('sd', 's', 'd', 'question'), edge('dc', 'd', 'c', 'draft'),
    { id: 'cd', source: 'c', target: 'd', target_port: 'previous', kind: 'feedback',
      loop_id: 'refine', initial_value: 'No previous critique' },
    edge('co', 'c', 'output', 'answer'),
  ]);
  graph.loops = [{ id: 'refine', node_ids: ['d', 'c'], controller_node_id: 'c', continue_value: 'continue', exit_value: 'stop' }];
  return graph;
}

export const portsFor = (graph: Graph, id: string): string[] => graph.edges
  .filter(e => e.target === id).map(e => e.target_port).sort();
export const encodeGraph = (graph: Graph): string => JSON.stringify(graph, null, 2);

// Research import guards cover editor fidelity; the backend owns publication validation.
export function decodeGraph(text: string): Graph {
  const graph: Graph = JSON.parse(text);
  if (!graph || graph.schema_version !== 1) throw new Error('schema_version must be 1');
  if (!Array.isArray(graph.nodes) || !Array.isArray(graph.edges) || !Array.isArray(graph.loops)) throw new Error('Missing graph arrays');
  const ids = new Set(graph.nodes.map(n => n.id));
  if (ids.size !== graph.nodes.length) throw new Error('Duplicate node ID');
  for (const node of graph.nodes) {
    if (!['input', 'llm', 'output'].includes(node.type) || !Number.isFinite(node.position?.x) || !Number.isFinite(node.position?.y)) throw new Error('Invalid node');
  }
  const providers = new Set<string>();
  for (const e of graph.edges) {
    if (!ids.has(e.source) || !ids.has(e.target)) throw new Error('Unknown edge endpoint');
    if (!e.target_port || !['forward', 'feedback'].includes(e.kind)) throw new Error('Invalid port or edge kind');
    const port = `${e.target}:${e.target_port}`;
    if (providers.has(port)) throw new Error(`${port} already has a provider`);
    providers.add(port);
    if (e.kind === 'feedback') {
      if (!Object.hasOwn(e, 'initial_value')) throw new Error('Feedback seed required (explicit null allowed)');
      const loop = graph.loops.find(l => l.id === e.loop_id);
      if (!loop || !loop.node_ids.includes(e.source) || !loop.node_ids.includes(e.target)) throw new Error('Feedback requires loop membership');
    }
  }
  for (const loop of graph.loops) {
    if (!loop.node_ids.every(id => ids.has(id)) || !loop.node_ids.includes(loop.controller_node_id)) throw new Error('Invalid loop controller or membership');
    if (!loop.continue_value || !loop.exit_value || loop.continue_value === loop.exit_value) throw new Error('Distinct continue and exit decisions required');
  }
  return graph;
}

export function addConnection(graph: Graph, source: string, target: string, port: string): Graph {
  if (graph.edges.some(e => e.target === target && e.target_port === port)) throw new Error(`${target}:${port} already has a provider`);
  const next = structuredClone(graph);
  next.edges.push(edge(`edge-${source}-${target}-${port}`, source, target, port));
  return decodeGraph(encodeGraph(next));
}
export function updatePrompt(graph: Graph, id: string, prompt: string): Graph {
  return { ...graph, nodes: graph.nodes.map(n => n.id === id ? { ...n, system_prompt: prompt } : n) };
}
