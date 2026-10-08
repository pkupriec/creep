import { useLayoutEffect, useState } from 'react';
import { Background, Controls, MarkerType, ReactFlow, applyNodeChanges, type Connection, type NodeChange } from '@xyflow/react';
import type { Edge, Graph, Node } from '../contracts/generated';
import { GraphNode, type CanvasNode } from './GraphNode';
import { connect, nextPort, parseValue, removeNode } from './graph';
const nodeTypes = { graph: GraphNode };
interface Props {
    graph: Graph;
    loadVersion: number;
    onChange: (graph: Graph) => void;
    models: string[];
    report: (message: string) => void;
}
export function Editor({ graph, loadVersion, onChange, models, report }: Props) {
    const [selected, setSelected] = useState<string>('');
    const [edgeSelected, setEdgeSelected] = useState<string>('');
    const [newId, setNewId] = useState('');
    const [newType, setNewType] = useState<Node['type']>('llm');
    const [port, setPort] = useState('');
    const [source, setSource] = useState('');
    const [target, setTarget] = useState('');
    const [kind, setKind] = useState<Edge['kind']>('forward');
    const [loopId, setLoopId] = useState('');
    const [seed, setSeed] = useState('null');
    const [scopeId, setScopeId] = useState('');
    const [controller, setController] = useState('');
    const [members, setMembers] = useState<string[]>([]);
    const [continueValue, setContinue] = useState('continue');
    const [exitValue, setExit] = useState('stop');
    const [generationDrafts, setGenerationDrafts] = useState<Record<string, string>>({});
    const [inputId, setInputId] = useState('');
    const [measurements, setMeasurements] = useState<Record<string, { width: number; height: number }>>({});
    const node = graph.nodes.find(item => item.id === selected);
    const edge = graph.edges.find(item => item.id === edgeSelected);
    const generation = node?.type === 'llm' ? generationDrafts[node.id] ?? JSON.stringify(node.generation, null, 2) : '{}';
    // Only an explicit authoritative load rebases drafts; local edits and saves keep them.
    useLayoutEffect(() => {
        setGenerationDrafts({});
        if (!graph.nodes.some(item => item.id === selected)) setSelected('');
        const loadedEdge = graph.edges.find(item => item.id === edgeSelected);
        setEdgeSelected(loadedEdge?.id ?? '');
        setSource(loadedEdge?.source ?? '');
        setTarget(loadedEdge?.target ?? '');
        setPort(loadedEdge?.target_port ?? '');
        setKind(loadedEdge?.kind ?? 'forward');
        setLoopId(loadedEdge?.kind === 'feedback' ? loadedEdge.loop_id : '');
        setSeed(loadedEdge?.kind === 'feedback' ? JSON.stringify(loadedEdge.initial_value) : 'null');
        const loadedScope = graph.loops.find(item => item.id === scopeId);
        setScopeId(loadedScope?.id ?? '');
        setController(loadedScope?.controller_node_id ?? '');
        setMembers(loadedScope?.node_ids ?? []);
        setContinue(loadedScope?.continue_value ?? 'continue');
        setExit(loadedScope?.exit_value ?? 'stop');
        setNewId('');
        setInputId('');
    }, [loadVersion]);
    const nodes: CanvasNode[] = graph.nodes.map((item, index) => ({ id: item.id, type: 'graph', position: item.position ?? { x: index * 260, y: 100 }, selected: item.id === selected, measured: measurements[item.id],
        data: { label: item.id, kind: item.type, scope: graph.loops.find(loop => loop.node_ids.includes(item.id))?.id ?? '',
            ports: item.type === 'input' ? [] : [...new Set(graph.edges.filter(edge => edge.target === item.id).map(edge => edge.target_port))].sort().concat(nextPort(graph, item.id)) } }));
    const edges = graph.edges.map(item => ({ id: item.id, source: item.source, target: item.target, sourceHandle: 'out', targetHandle: item.target_port,
        label: `${item.target_port}${item.kind === 'feedback' ? ` ↻ ${item.loop_id}` : ''}`, type: item.kind === 'feedback' ? 'smoothstep' : 'default',
        style: { stroke: item.kind === 'feedback' ? '#b65c20' : '#547687', strokeWidth: 2, strokeDasharray: item.kind === 'feedback' ? '6 4' : undefined },
        markerEnd: { type: MarkerType.ArrowClosed }, selected: item.id === edgeSelected }));
    function attempt(action: () => void) { try {
        action();
    }
    catch (error) {
        report(error instanceof Error ? error.message : String(error));
    } }
    function updateNode(patch: Partial<Node>) { if (node)
        onChange({ ...graph, nodes: graph.nodes.map(item => item.id === node.id ? { ...item, ...patch } as Node : item) }); }
    function onNodesChange(changes: NodeChange<CanvasNode>[]) {
        // React Flow measurements are browser state, never graph execution data.
        setMeasurements(current => {
            let next = current;
            for (const change of changes) {
                if (change.type === 'dimensions' && change.dimensions &&
                    (current[change.id]?.width !== change.dimensions.width || current[change.id]?.height !== change.dimensions.height)) {
                    next = { ...next, [change.id]: change.dimensions };
                }
                if (change.type === 'remove' && next[change.id]) {
                    next = { ...next };
                    delete next[change.id];
                }
            }
            return next;
        });
        if (!changes.some(change => change.type === 'position' || change.type === 'remove')) return;
        const removed = changes.filter(change => change.type === 'remove').map(change => change.id);
        let next = graph;
        for (const id of removed)
            next = removeNode(next, id);
        const changed = applyNodeChanges(changes, nodes);
        onChange({ ...next, nodes: next.nodes.map(item => ({ ...item, position: changed.find(n => n.id === item.id)?.position ?? item.position })) });
    }
    function addConnection(connection: Connection) {
        attempt(() => {
            if (!connection.source || !connection.target)
                return;
            const targetNode = graph.nodes.find(item => item.id === connection.target);
            if (targetNode?.type === 'input')
                throw new Error('Input nodes have no incoming ports.');
            if (kind === 'feedback' && !graph.loops.some(loop => loop.id === loopId))
                throw new Error('Create a loop scope with members, controller and exit condition first.');
            const base = { id: `e_${crypto.randomUUID().replaceAll('-', '').slice(0, 12)}`, source: connection.source, target: connection.target, target_port: connection.targetHandle ?? nextPort(graph, connection.target) };
            onChange(connect(graph, kind === 'feedback' ? { ...base, kind, loop_id: loopId, initial_value: parseValue(seed) } : { ...base, kind }));
        });
    }
    function addEdge() {
        attempt(() => {
            const id = edge?.id ?? `e_${crypto.randomUUID().replaceAll('-', '').slice(0, 12)}`;
            const next: Edge = kind === 'feedback' ? { id, source, target, target_port: port, kind, loop_id: loopId, initial_value: parseValue(seed) } : { id, source, target, target_port: port, kind };
            if (!source || !target || !port)
                throw new Error('Choose a source, target and named port.');
            if (kind === 'feedback' && !graph.loops.some(loop => loop.id === loopId))
                throw new Error('Create a loop scope with members, controller and exit condition first.');
            onChange(connect(graph, next));
            setEdgeSelected('');
        });
    }
    return <div className="editor">
    <div className="canvas" aria-label="Graph canvas"><ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodesChange={onNodesChange} onEdgesDelete={deleted => onChange({ ...graph, edges: graph.edges.filter(item => !deleted.some(edge => edge.id === item.id)) })} onNodeClick={(_, item) => { setSelected(item.id); }} onEdgeClick={(_, item) => { const found = graph.edges.find(edge => edge.id === item.id)!; setEdgeSelected(found.id); setSource(found.source); setTarget(found.target); setPort(found.target_port); setKind(found.kind); setLoopId(found.kind === 'feedback' ? found.loop_id : ''); setSeed(found.kind === 'feedback' ? JSON.stringify(found.initial_value) : 'null'); }} onConnect={addConnection} fitView minZoom={0.2} maxZoom={2} deleteKeyCode={['Backspace', 'Delete']}><Background /><Controls /></ReactFlow></div>
    <aside className="inspector">
      <h2>Graph settings</h2>
      <label>Name<input value={graph.name} onChange={event => onChange({ ...graph, name: event.target.value })}/></label>
      <label>Base model<select aria-label="Base model" value={graph.base_model} onChange={event => onChange({ ...graph, base_model: event.target.value })}>
        {!models.includes(graph.base_model) && <option value={graph.base_model}>{graph.base_model} (unavailable)</option>}{models.map(model => <option key={model}>{model}</option>)}</select></label>
      <h3>Named inputs</h3>
      {graph.inputs.map(input => <div className="row" key={input.id}><code>{input.id}</code><label><input type="checkbox" checked={input.required} onChange={event => onChange({ ...graph, inputs: graph.inputs.map(item => item.id === input.id ? { ...item, required: event.target.checked } : item) })}/>Required</label>
        <button onClick={() => onChange({ ...graph, inputs: graph.inputs.filter(item => item.id !== input.id) })} aria-label={`Remove input ${input.id}`}>×</button></div>)}
      <div className="row"><input aria-label="New input name" value={inputId} onChange={event => setInputId(event.target.value)}/><button onClick={() => attempt(() => { if (!inputId || graph.inputs.some(item => item.id === inputId))
        throw new Error('Choose a unique input name.'); onChange({ ...graph, inputs: [...graph.inputs, { id: inputId, required: true }] }); setInputId(''); })}>Add input</button></div>
      <h3>Add node</h3><label>Node ID<input value={newId} onChange={event => setNewId(event.target.value)}/></label>
      <select aria-label="Node type" value={newType} onChange={event => setNewType(event.target.value as Node['type'])}><option>llm</option><option>input</option><option>output</option></select>
      <button onClick={() => attempt(() => { if (!newId || graph.nodes.some(item => item.id === newId))
        throw new Error('Choose a unique node ID.'); const position = { x: graph.nodes.length * 100, y: 260 }; const added: Node = newType === 'llm' ? { id: newId, type: newType, system_prompt: '', tools_enabled: false, generation: {}, position } : newType === 'input' ? { id: newId, type: newType, input_id: graph.inputs[0]?.id ?? 'chat', position } : { id: newId, type: newType, position }; onChange({ ...graph, nodes: [...graph.nodes, added] }); setSelected(newId); setNewId(''); setGenerationDrafts(current => ({ ...current, [newId]: "{}" })); })}>Add node</button>
      {node && <section><h3>Node: {node.id}</h3>
        {node.type === 'llm' && <><label>System prompt<textarea rows={5} value={node.system_prompt} onChange={event => updateNode({ system_prompt: event.target.value })}/></label><label><input type="checkbox" checked={node.tools_enabled} onChange={event => updateNode({ tools_enabled: event.target.checked })}/>Tools enabled</label>
          <label>Generation settings (JSON)<textarea rows={4} value={generation} onChange={event => { const text = event.target.value; setGenerationDrafts(current => ({ ...current, [node.id]: text })); }}/></label><button onClick={() => attempt(() => updateNode({ generation: JSON.parse(generation) }))}>Apply generation settings</button></>}
        {node.type === 'input' && <label>Named input<select aria-label="Named input" value={node.input_id} onChange={event => updateNode({ input_id: event.target.value })}>{graph.inputs.map(item => <option key={item.id}>{item.id}</option>)}</select></label>}
        {node.type === 'output' && <button onClick={() => onChange({ ...graph, output_node_id: node.id })}>Use as terminal output</button>}
        <button className="danger" onClick={() => { onChange(removeNode(graph, node.id)); setSelected(''); }}>Delete node</button></section>}
      <h3>{edge ? 'Edit connection' : 'Add connection'}</h3>
      <label>Source<select aria-label="Source" value={source} onChange={event => setSource(event.target.value)}><option value="">Select node</option>{graph.nodes.filter(n => n.type !== 'output').map(n => <option key={n.id}>{n.id}</option>)}</select></label>
      <label>Target<select aria-label="Target" value={target} onChange={event => setTarget(event.target.value)}><option value="">Select node</option>{graph.nodes.filter(n => n.type !== 'input').map(n => <option key={n.id}>{n.id}</option>)}</select></label>
      <label>Target port<input value={port} onChange={event => setPort(event.target.value)}/></label>
      <label>Connection kind<select aria-label="Connection kind" value={kind} onChange={event => setKind(event.target.value as Edge['kind'])}><option>forward</option><option>feedback</option></select></label>
      {kind === 'feedback' && <><label>Loop scope<select aria-label="Loop scope" value={loopId} onChange={event => setLoopId(event.target.value)}><option value="">Choose scope</option>{graph.loops.map(loop => <option key={loop.id}>{loop.id}</option>)}</select></label><label>Feedback seed (JSON, including null)<textarea value={seed} onChange={event => setSeed(event.target.value)}/></label></>}
      <button onClick={addEdge}>{edge ? 'Apply connection' : 'Add connection'}</button>
      {edge && <><button onClick={() => setEdgeSelected('')}>New connection</button><button className="danger" onClick={() => { onChange({ ...graph, edges: graph.edges.filter(item => item.id !== edge.id) }); setEdgeSelected(''); }}>Delete connection</button></>}
      <h3>Loop scopes</h3>
      {graph.loops.map(loop => <div key={loop.id}><button onClick={() => { setScopeId(loop.id); setController(loop.controller_node_id); setMembers(loop.node_ids); setContinue(loop.continue_value); setExit(loop.exit_value); }}>{loop.id}</button><button aria-label={`Delete scope ${loop.id}`} onClick={() => onChange({ ...graph, loops: graph.loops.filter(item => item.id !== loop.id), edges: graph.edges.filter(edge => edge.kind !== 'feedback' || edge.loop_id !== loop.id) })}>×</button></div>)}
      <label>Scope ID<input value={scopeId} onChange={event => setScopeId(event.target.value)}/></label>
      <fieldset><legend>Scope members</legend>{graph.nodes.filter(n => n.type !== 'output').map(n => <label key={n.id}><input type="checkbox" checked={members.includes(n.id)} onChange={event => setMembers(event.target.checked ? [...members, n.id] : members.filter(id => id !== n.id))}/>{n.id}</label>)}</fieldset>
      <label>Controller<select aria-label="Controller" value={controller} onChange={event => setController(event.target.value)}><option value="">Select LLM</option>{graph.nodes.filter(n => n.type === 'llm').map(n => <option key={n.id}>{n.id}</option>)}</select></label>
      <label>Continue value<input value={continueValue} onChange={event => setContinue(event.target.value)}/></label><label>Exit value<input value={exitValue} onChange={event => setExit(event.target.value)}/></label>
      <button onClick={() => attempt(() => { if (!scopeId || !members.includes(controller) || continueValue === exitValue || !continueValue || !exitValue)
        throw new Error('Choose members, a member controller and different continue/exit values.'); if (graph.loops.some(loop => loop.id !== scopeId && loop.node_ids.some(id => members.includes(id))))
        throw new Error('Loop scopes must be disjoint.'); onChange({ ...graph, loops: [...graph.loops.filter(loop => loop.id !== scopeId), { id: scopeId, node_ids: members, controller_node_id: controller, continue_value: continueValue, exit_value: exitValue }] }); })}>Apply loop scope</button>
      <p className="muted">Coordinates affect the view. Every connected input port waits for its provider. Feedback starts with its seed; only the controller exit releases the loop output.</p>
    </aside>
  </div>;
}
