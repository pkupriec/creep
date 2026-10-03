import { useCallback, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Background, BaseEdge, Controls, Handle, MarkerType, Position, ReactFlow, applyEdgeChanges, applyNodeChanges, useUpdateNodeInternals, type Connection, type Edge, type EdgeProps, type Node, type NodeProps } from '@xyflow/react';
import { ClassicPreset, NodeEditor, type GetSchemes } from 'rete';
import { AreaExtensions, AreaPlugin } from 'rete-area-plugin';
import { ConnectionPlugin, Presets as ConnectionPresets } from 'rete-connection-plugin';
import { Presets as RetePresets, ReactPlugin, type ReactArea2D } from 'rete-react-plugin';
import { css, StyleSheetManager } from 'styled-components';
import { addConnection, createDiamond, createLoop, decodeGraph, encodeGraph, portsFor, updatePrompt, type Graph, type GraphNode } from './graph';
import '@xyflow/react/dist/style.css';
import './style.css';

type ThoughtNode = Node<{ node: GraphNode; ports: string[]; membership: string; controller: boolean }, 'thought'>;
function Thought({ data }: NodeProps<ThoughtNode>) {
  const { node, ports, membership, controller } = data;
  const updateInternals = useUpdateNodeInternals();
  useEffect(() => updateInternals(node.id), [node.id, ports.join(','), updateInternals]);
  const inputs = node.type === 'input' ? [] : [...ports, 'extra'];
  return <div className={`thought ${membership ? 'loop-member' : ''}`} data-testid={`node-${node.id}`}>
    <small>{node.type.toUpperCase()}{controller ? ' · CONTROLLER' : ''}</small>
    <strong>{node.id}</strong>
    {membership && <span className="badge">Loop: {membership}</span>}
    {inputs.map((port, index) => <div key={port} className="port" style={{ top: 84 + index * 27 }}>
      <Handle type="target" id={port} position={Position.Left} data-testid={`target-${node.id}-${port}`} style={{ top: 12 }} />
      <span>{port === 'extra' ? '+ new port' : port}</span>
    </div>)}
    <p style={{ marginTop: Math.max(12, inputs.length * 27 + 30) }}>{node.system_prompt ?? (node.type === 'input' ? `${node.input_id} input` : 'Final payload')}</p>
    {node.type !== 'output' && <Handle type="source" id="payload" position={Position.Right} data-testid={`source-${node.id}`} />}
  </div>;
}
function FeedbackArc(props: EdgeProps) {
  const { sourceX, sourceY, targetX, targetY } = props;
  const arcY = Math.min(sourceY, targetY) - 155;
  const path = `M ${sourceX} ${sourceY} C ${sourceX + 100} ${arcY}, ${targetX - 100} ${arcY}, ${targetX} ${targetY}`;
  return <><BaseEdge id={props.id} path={path} style={props.style} markerEnd={props.markerEnd} /><text x={(sourceX + targetX) / 2} y={arcY + 32} textAnchor="middle" className="feedback-label">feedback · next iteration</text></>;
}
const nodeTypes = { thought: Thought };
const edgeTypes = { feedback: FeedbackArc };
type CanvasProps = { graph: Graph; change: (graph: Graph) => void; select: (id: string) => void; connect: (connection: Connection) => void };

function FlowCanvas({ graph, change, select, connect }: CanvasProps) {
  const project = useCallback((): ThoughtNode[] => graph.nodes.map(node => ({
    id: node.id, type: 'thought', position: node.position, deletable: false,
    data: { node, ports: portsFor(graph, node.id), membership: graph.loops.find(l => l.node_ids.includes(node.id))?.id ?? '', controller: graph.loops.some(l => l.controller_node_id === node.id) },
  })), [graph]);
  const [nodes, setNodes] = useState(project);
  const projectEdges = useCallback((): Edge[] => graph.edges.map(e => ({
    id: e.id, source: e.source, target: e.target, sourceHandle: 'payload', targetHandle: e.target_port,
    type: e.kind === 'feedback' ? 'feedback' : 'default',
    label: e.kind === 'forward' ? e.target_port : undefined,
    markerEnd: { type: MarkerType.ArrowClosed, color: e.kind === 'feedback' ? '#ec8b38' : '#8395b5' },
    style: { stroke: e.kind === 'feedback' ? '#ec8b38' : '#8395b5', strokeWidth: 2, strokeDasharray: e.kind === 'feedback' ? '7 4' : undefined },
  })), [graph]);
  const [edges, setEdges] = useState(projectEdges);
  const previousGraph = useRef(graph);
  useEffect(() => {
    if (previousGraph.current === graph) return;
    previousGraph.current = graph;
    setNodes(current => project().map(node => ({ ...current.find(n => n.id === node.id), ...node })));
    setEdges(current => projectEdges().map(edge => ({ ...current.find(e => e.id === edge.id), ...edge })));
  }, [graph, project, projectEdges]);
  return <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes}
    onNodesChange={changes => setNodes(current => applyNodeChanges(changes, current))}
    onEdgesChange={changes => setEdges(current => applyEdgeChanges(changes, current))}
    onNodeDragStop={(_, node) => change({ ...graph, nodes: graph.nodes.map(n => n.id === node.id ? { ...n, position: node.position } : n) })}
    onNodeClick={(_, node) => select(node.id)} onConnect={connect}
    onEdgesDelete={removed => change({ ...graph, edges: graph.edges.filter(e => !removed.some(r => r.id === e.id)) })}
    deleteKeyCode="Delete" fitView minZoom={0.2} maxZoom={2}>
    <Background gap={24} color="#273246" /><Controls />
  </ReactFlow>;
}

class ReteNode extends ClassicPreset.Node {
  constructor(public original: GraphNode, public membership: string, public controller: boolean) {
    super(`${original.id} · ${original.type}${controller ? ' · controller' : ''}${membership ? ` · loop ${membership}` : ''}`);
    this.id = original.id;
  }
}
class ReteConnection extends ClassicPreset.Connection<ReteNode, ReteNode> {
  feedback = false;
}
type Schemes = GetSchemes<ReteNode, ReteConnection>;
type AreaExtra = ReactArea2D<Schemes>;
function ReteNodeView(props: { data: ReteNode; emit: RetePresets.classic.RenderEmit<Schemes> }) {
  return <div data-testid={`rete-node-${props.data.id}`}><StyleSheetManager shouldForwardProp={name => name !== 'styles'}><RetePresets.classic.Node {...props} styles={() => css`
    background: #182338; border: 1px solid ${props.data.membership ? '#ec8b38' : '#7287ab'}; border-radius: 10px;
    width: 220px; color: #f2f5fa; font-size: 13px;
  `} /></StyleSheetManager></div>;
}
function ReteConnectionView({ data }: { data: ReteConnection }) {
  return <div data-testid={`rete-edge-${data.id}`} data-kind={data.feedback ? 'feedback' : 'forward'}>
    <StyleSheetManager shouldForwardProp={name => name !== 'styles'}><RetePresets.classic.Connection data={{ ...data, isLoop: data.feedback }} styles={() => css`
      stroke: ${data.feedback ? '#ec8b38' : '#8395b5'}; stroke-width: 2px; stroke-dasharray: ${data.feedback ? '7 4' : 'none'};
    `} /></StyleSheetManager>
  </div>;
}
function ReteCanvas({ graph, change, select, connect }: CanvasProps) {
  const container = useRef<HTMLDivElement>(null);
  const latest = useRef({ graph, change, select, connect });
  latest.current = { graph, change, select, connect };
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    if (!container.current) return;
    let closed = false;
    let importing = true;
    setReady(false);
    const editor = new NodeEditor<Schemes>();
    const area = new AreaPlugin<Schemes, AreaExtra>(container.current);
    const render = new ReactPlugin<Schemes, AreaExtra>({ createRoot });
    const connections = new ConnectionPlugin<Schemes, AreaExtra>();
    connections.addPreset(ConnectionPresets.classic.setup());
    render.addPreset(RetePresets.classic.setup<Schemes, AreaExtra>({ customize: { node: () => ReteNodeView, connection: () => ReteConnectionView } }));
    editor.use(area); area.use(render); area.use(connections);
    AreaExtensions.selectableNodes(area, AreaExtensions.selector(), { accumulating: AreaExtensions.accumulateOnCtrl() });
    editor.addPipe(context => {
      if (!importing && context.type === 'connectioncreate') {
        const c = context.data;
        latest.current.connect({ source: c.source, target: c.target, sourceHandle: c.sourceOutput, targetHandle: c.targetInput });
        return;
      }
      return context;
    });
    area.addPipe(context => {
      if (context.type === 'nodepicked') latest.current.select(context.data.id);
      if (!importing && context.type === 'nodedragged') {
        const positions = area.nodeViews;
        const current = latest.current.graph;
        latest.current.change({ ...current, nodes: current.nodes.map(n => ({ ...n, position: positions.get(n.id)?.position ?? n.position })) });
      }
      return context;
    });
    async function load() {
      const socket = new ClassicPreset.Socket('payload');
      const nodes = new Map<string, ReteNode>();
      for (const original of graph.nodes) {
        if (closed) return;
        const loop = graph.loops.find(l => l.node_ids.includes(original.id));
        const node = new ReteNode(original, loop?.id ?? '', loop?.controller_node_id === original.id);
        if (original.type !== 'input') {
          for (const port of [...portsFor(graph, original.id), 'extra']) node.addInput(port, new ClassicPreset.Input(socket, port, false));
        }
        if (original.type !== 'output') node.addOutput('payload', new ClassicPreset.Output(socket, 'payload', true));
        if (original.type === 'llm') node.addControl('prompt', new ClassicPreset.InputControl('text', {
          initial: original.system_prompt ?? '', change: value => {
            if (!closed) latest.current.change(updatePrompt(latest.current.graph, node.id, String(value)));
          },
        }));
        await editor.addNode(node); nodes.set(node.id, node);
        await area.translate(node.id, original.position);
      }
      for (const e of graph.edges) {
        if (closed) return;
        const c = new ReteConnection(nodes.get(e.source)!, 'payload', nodes.get(e.target)!, e.target_port);
        c.id = e.id; c.feedback = e.kind === 'feedback';
        await editor.addConnection(c);
      }
      if (closed) return;
      await AreaExtensions.zoomAt(area, editor.getNodes());
      importing = false; setReady(true);
    }
    load().catch(e => { if (!closed) setError(String(e)); });
    return () => { closed = true; area.destroy(); };
  }, [graph]);
  return <><div className="rete-canvas" ref={container} data-testid="rete-canvas" data-ready={ready} />{error && <p role="alert">{error}</p>}</>;
}

function App() {
  const [graph, setGraph] = useState(createLoop);
  const [library, setLibrary] = useState<'flow' | 'rete'>('flow');
  const [selected, select] = useState('d');
  const [json, setJson] = useState('');
  const [message, setMessage] = useState('');
  const [portName, setPortName] = useState('context');
  const [edgeKind, setEdgeKind] = useState<'forward' | 'feedback'>('forward');
  const [pending, setPending] = useState<Connection | null>(null);
  const [loopId, setLoopId] = useState('refine');
  const [members, setMembers] = useState(['d', 'c']);
  const [controller, setController] = useState('c');
  const [seed, setSeed] = useState('"No previous critique"');
  const [continueValue, setContinueValue] = useState('continue');
  const [exitValue, setExitValue] = useState('stop');
  const node = graph.nodes.find(n => n.id === selected);
  function change(next: Graph) { setGraph(next); setMessage('Graph updated'); }
  function connect(c: Connection) {
    if (edgeKind === 'feedback') { setPending(c); return; }
    try { change(addConnection(graph, c.source, c.target, c.targetHandle === 'extra' ? portName : c.targetHandle ?? portName)); }
    catch (e) { setMessage(String(e)); }
  }
  function applyFeedback() {
    try {
      if (!pending) return;
      const next = addConnection(graph, pending.source, pending.target, pending.targetHandle === 'extra' ? portName : pending.targetHandle ?? portName);
      next.edges[next.edges.length - 1] = { ...next.edges[next.edges.length - 1], kind: 'feedback', loop_id: loopId, initial_value: JSON.parse(seed) };
      next.loops = next.loops.filter(l => l.id !== loopId).concat([{ id: loopId, node_ids: members, controller_node_id: controller, continue_value: continueValue, exit_value: exitValue }]);
      change(decodeGraph(encodeGraph(next))); setPending(null);
    } catch (e) { setMessage(String(e)); }
  }
  function editLoop(field: 'continue_value' | 'exit_value' | 'controller_node_id', value: string) {
    change({ ...graph, loops: graph.loops.map(l => l.id === loopId ? { ...l, [field]: value } : l) });
  }
  return <main>
    <header><div><span className="eyebrow">RD2 · G0 RESEARCH</span><h1>Cognitive Graph editor</h1><p>Named inputs, all-input synthesis and explicit seeded feedback</p></div>
      <nav aria-label="Editor comparison"><button className={library === 'flow' ? 'active' : ''} onClick={() => setLibrary('flow')}>React Flow</button><button className={library === 'rete' ? 'active' : ''} onClick={() => setLibrary('rete')}>Rete.js</button></nav>
    </header>
    <section className="toolbar"><button onClick={() => { change(createDiamond()); select('a'); }}>Diamond</button><button onClick={() => { change(createLoop()); select('d'); }}>Seeded loop</button>
      <label>Connection type<select aria-label="Connection type" value={edgeKind} onChange={e => setEdgeKind(e.target.value as 'forward' | 'feedback')}><option value="forward">Forward</option><option value="feedback">Feedback</option></select></label>
      <label>New port name<input aria-label="New port name" value={portName} onChange={e => setPortName(e.target.value)} /></label>
      <button onClick={() => { setJson(encodeGraph(graph)); setMessage('JSON exported'); }}>Export JSON</button>
      <button onClick={() => { try { change(decodeGraph(json)); setMessage('JSON imported'); } catch (e) { setMessage(String(e)); } }}>Import JSON</button>
      <span role="status">{message || `${graph.nodes.length} nodes · ${graph.edges.length} edges`}</span>
    </section>
    <div className="workspace"><section className="canvas" aria-label={`${library === 'flow' ? 'React Flow' : 'Rete'} canvas`}>
      {library === 'flow' ? <FlowCanvas graph={graph} change={change} select={select} connect={connect} /> : <ReteCanvas graph={graph} change={change} select={select} connect={connect} />}
      <div className="legend"><span>━━ forward</span><span className="orange">┄┄ feedback · seeded next iteration</span><span>Drag nodes · zoom/pan · select edge + Delete (React Flow)</span></div>
    </section>
    <aside><h2>Node and loop settings</h2><label>Selected node<select aria-label="Selected node" value={selected} onChange={e => select(e.target.value)}>{graph.nodes.map(n => <option key={n.id}>{n.id}</option>)}</select></label>
      {node?.type === 'llm' && <label>System prompt<textarea aria-label="System prompt" rows={4} value={node.system_prompt} onChange={e => change(updatePrompt(graph, node.id, e.target.value))} /></label>}
      <p className="note">Backend waits for every named input. Canvas position never schedules execution.</p>
      <h3>{pending ? 'Configure new feedback' : 'Loop contract'}</h3>
      {pending && <p>{pending.source} → {pending.target}; configure before committing</p>}
      <label>Scope ID<input aria-label="Scope ID" value={loopId} onChange={e => setLoopId(e.target.value)} /></label>
      <fieldset><legend>Members</legend>{graph.nodes.filter(n => n.type === 'llm').map(n => <label className="check" key={n.id}><input aria-label={`Member ${n.id}`} type="checkbox" checked={pending ? members.includes(n.id) : graph.loops.find(l => l.id === loopId)?.node_ids.includes(n.id) ?? false} onChange={e => {
        if (pending) setMembers(current => e.target.checked ? [...current, n.id] : current.filter(id => id !== n.id));
        else change({ ...graph, loops: graph.loops.map(l => l.id === loopId ? { ...l, node_ids: e.target.checked ? [...l.node_ids, n.id] : l.node_ids.filter(id => id !== n.id) } : l) });
      }} />{n.id}</label>)}</fieldset>
      <label>Controller<select aria-label="Controller" value={pending ? controller : graph.loops.find(l => l.id === loopId)?.controller_node_id ?? controller} onChange={e => pending ? setController(e.target.value) : editLoop('controller_node_id', e.target.value)}>{graph.nodes.filter(n => n.type === 'llm').map(n => <option key={n.id}>{n.id}</option>)}</select></label>
      <label>Feedback seed (JSON)<input aria-label="Feedback seed" value={seed} onChange={e => setSeed(e.target.value)} onBlur={() => { if (!pending) { try { const initial_value = JSON.parse(seed); change({ ...graph, edges: graph.edges.map(e => e.loop_id === loopId ? { ...e, initial_value } : e) }); } catch (e) { setMessage(String(e)); } } }} /></label>
      <div className="decisions"><label>Continue<input aria-label="Continue decision" value={pending ? continueValue : graph.loops.find(l => l.id === loopId)?.continue_value ?? continueValue} onChange={e => pending ? setContinueValue(e.target.value) : editLoop('continue_value', e.target.value)} /></label><label>Exit<input aria-label="Exit decision" value={pending ? exitValue : graph.loops.find(l => l.id === loopId)?.exit_value ?? exitValue} onChange={e => pending ? setExitValue(e.target.value) : editLoop('exit_value', e.target.value)} /></label></div>
      {pending && <><button onClick={applyFeedback}>Commit feedback</button><button onClick={() => setPending(null)}>Cancel feedback</button></>}
      <p className="note">Controller emits payload with strict control.decision. Only stop releases the final payload. No scheduler runs here.</p>
    </aside></div>
    <details open><summary>Canonical graph JSON · schema_version 1</summary><textarea aria-label="Graph JSON" value={json} onChange={e => setJson(e.target.value)} placeholder="Export the graph, then import it to test round-trip fidelity." /></details>
  </main>;
}
createRoot(document.getElementById('root')!).render(<App />);
