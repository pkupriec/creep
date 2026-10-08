import { useEffect, useMemo, useRef, useState } from 'react';
import { ApiClient, ApiError } from './api/client';
import type { Graph, GraphListResponse, HealthResponse, ModelsResponse, PublishGraphResponse, StartRunResponse, ValidationReport } from './contracts/generated';
import { Editor } from './editor/Editor';
import { createGraph, exportGraph, importGraph } from './editor/graph';
import { History } from './runs/History';
import { RunDetail } from './runs/RunDetail';
export function App() {
    const [token, setToken] = useState(''), tokenRef = useRef('');
    tokenRef.current = token;
    const client = useMemo(() => new ApiClient(() => tokenRef.current), []);
    const [graphs, setGraphs] = useState<GraphListResponse['graphs']>([]), [models, setModels] = useState<string[]>([]);
    const [graph, setGraph] = useState<Graph | null>(null), [saved, setSaved] = useState(''), [error, setError] = useState(''), [notice, setNotice] = useState('');
    const [ready, setReady] = useState<HealthResponse | null>(null), [newId, setNewId] = useState(''), [newName, setNewName] = useState(''), [newModel, setNewModel] = useState('');
    const [importText, setImportText] = useState(''), [runInputs, setRunInputs] = useState('{}'), [tools, setTools] = useState('[]');
    const [busy, setBusy] = useState(false), [activeRun, setActiveRun] = useState(''), [tab, setTab] = useState<'editor' | 'history'>('editor'), [refreshKey, setRefreshKey] = useState(0);
    const [conflict, setConflict] = useState(false), [report, setReport] = useState<ValidationReport | null>(null);
    const [graphLoadVersion, setGraphLoadVersion] = useState(0);
    const dirty = !!graph && JSON.stringify(graph) !== saved;
    async function refresh() {
        const [list, physical] = await Promise.all([client.json<GraphListResponse>('/api/graphs'), client.json<ModelsResponse>('/v1/models')]);
        setGraphs(list.graphs);
        const names = physical.data.filter(model => model.owned_by === 'ollama' && model.id.startsWith('ollama/')).map(model => model.id.slice(7));
        setModels(names);
        setNewModel(current => names.includes(current) ? current : (names[0] ?? ''));
    }
    useEffect(() => { const controller = new AbortController(); client.json<HealthResponse>('/health/ready', { signal: controller.signal }).then(setReady).catch(() => { if (!controller.signal.aborted)
        setReady(null); }); return () => controller.abort(); }, [client, refreshKey]);
    async function action(callback: () => Promise<void>) { setBusy(true); setError(''); setNotice(''); try {
        await callback();
    }
    catch (error) {
        setError((error as Error).message);
        if (error instanceof ApiError && error.status === 409)
            setConflict(true);
    }
    finally {
        setBusy(false);
    } }
    function loaded(value: Graph, replaceInspectors = true) { setGraph(value); setSaved(JSON.stringify(value)); setConflict(false); setReport(null); setRunInputs(JSON.stringify(Object.fromEntries(value.inputs.filter(input => input.required).map(input => [input.id, ''])), null, 2)); if (replaceInspectors) setGraphLoadVersion(version => version + 1); }
    async function save(): Promise<Graph> { if (!graph)
        throw new Error('Open a graph first.'); const validated = importGraph(JSON.stringify(graph)); const value = await client.json<Graph>(`/api/graphs/${encodeURIComponent(graph.id)}`, { method: 'PUT', body: JSON.stringify({ graph: validated, expected_revision: graph.revision }) }); loaded(value, false); await refresh(); return value; }
    return <div className="app"><header><div><h1>Cognitive Graph</h1><p>Build a graph, publish it as a model, inspect each run.</p></div><div className="access"><label>API token<input type="password" autoComplete="off" value={token} onChange={event => { setToken(event.target.value); setGraphs([]); setActiveRun(''); setRefreshKey(key => key + 1); }}/></label><button disabled={busy} onClick={() => action(refresh)}>Connect / refresh</button><small>Token stays in memory. Re-enter after reload.</small></div></header>
    <div className="health" role="status">Storage: {ready?.storage_ready ? 'ready' : 'unavailable'} · Ollama: {ready?.ollama_available ? 'available' : 'unavailable'}</div>
    {error && <p className="banner error" role="alert">{error}</p>}{notice && <p className="banner" role="status">{notice}</p>}
    {conflict && <p className="banner">The server revision changed. Your edits are still here. Export them or reload the server version before saving again. <button onClick={() => graph && action(async () => loaded(await client.json<Graph>(`/api/graphs/${encodeURIComponent(graph.id)}`)))}>Reload server version</button></p>}
    <nav><button aria-pressed={tab === 'editor'} onClick={() => setTab('editor')}>Graph editor</button><button aria-pressed={tab === 'history'} onClick={() => { setTab('history'); setRefreshKey(key => key + 1); }}>History</button></nav>
    {tab === 'editor' ? <div className="workspace"><aside className="graph-list"><h2>Graphs</h2>{graphs.map(item => <button className="graph-entry" key={item.id} disabled={busy} onClick={() => action(async () => loaded(await client.json<Graph>(`/api/graphs/${encodeURIComponent(item.id)}`)))}><strong>{item.name}</strong><span>{item.id} · r{item.revision} · {item.published_revision ? `published r${item.published_revision}` : 'draft'}</span></button>)}
      <h3>Create graph</h3><label>Graph ID<input value={newId} onChange={event => setNewId(event.target.value)}/></label><label>Graph name<input value={newName} onChange={event => setNewName(event.target.value)}/></label><label>Installed model<select value={newModel} onChange={event => setNewModel(event.target.value)}><option value="">Connect to load models</option>{models.map(model => <option key={model}>{model}</option>)}</select></label>
      <button disabled={busy || !newModel} onClick={() => action(async () => { const value = await client.json<Graph>('/api/graphs', { method: 'POST', body: JSON.stringify(createGraph(newId, newName, newModel)) }); loaded(value); await refresh(); setNotice('Graph created.'); })}>Create graph</button>
      <details><summary>Import graph</summary><label>Graph JSON<textarea rows={9} value={importText} onChange={event => setImportText(event.target.value)}/></label><label>Import JSON file<input type="file" accept=".json,application/json" onChange={event => { const file = event.target.files?.[0]; if (file && file.size <= 512 * 1024)
            file.text().then(setImportText);
        else if (file)
            setError('Graph exceeds the size limit.'); }}/></label><p>Use a new ID to create a copy. To replace the open graph, keep its ID and use the current revision.</p>
      <button disabled={busy} onClick={() => action(async () => { const imported = importGraph(importText); if (graph && imported.id === graph.id) {
            loaded({ ...imported, revision: graph.revision });
            setSaved('');
            setNotice('Import loaded. Review and save against the current revision.');
        }
        else {
            loaded(await client.json<Graph>('/api/graphs', { method: 'POST', body: JSON.stringify({ ...imported, revision: 1 }) }));
            await refresh();
            setNotice('Graph imported.');
        } })}>Import graph</button></details>
    </aside><main>{graph ? <><div className="toolbar"><strong>{graph.name} · revision {graph.revision}{dirty ? ' · unsaved' : ''}</strong><button disabled={busy} onClick={() => action(async () => { await save(); setNotice('Graph saved.'); })}>Save graph</button><button disabled={busy || dirty} onClick={() => action(async () => { setReport(await client.json<ValidationReport>(`/api/graphs/${encodeURIComponent(graph.id)}/validate`, { method: 'POST' })); })}>Validate</button>
      <button disabled={busy || dirty} onClick={() => action(async () => { const response = await client.json<PublishGraphResponse>(`/api/graphs/${encodeURIComponent(graph.id)}/publish`, { method: 'POST', body: JSON.stringify({ expected_revision: graph.revision }) }); await refresh(); setNotice(`Published cg/${response.graph_id} revision ${response.published_revision}.`); })}>Publish revision</button>
      <button onClick={() => { try {
                const blob = new Blob([exportGraph(graph)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const anchor = document.createElement('a');
                anchor.href = url;
                anchor.download = `${graph.id}.json`;
                anchor.click();
                URL.revokeObjectURL(url);
            }
            catch (error) {
                setError((error as Error).message);
            } }}>Export graph</button></div>
      {report && <div className="banner"><strong>{report.valid ? 'Graph is valid' : 'Graph validation failed'}</strong>{[...report.errors, ...report.warnings].map((issue, index) => <p key={index}>{issue.node_id || issue.edge_id || 'Graph'}: {issue.message}</p>)}</div>}
      <Editor key={graph.id} graph={graph} loadVersion={graphLoadVersion} models={models} onChange={value => { setGraph(value); setReport(null); }} report={setError}/>
      <section className="test-run"><h2>Test graph</h2><p>Save edits before starting. Each run keeps its own immutable graph revision.</p><p>Inputs: {graph.inputs.map(input => `${input.id}${input.required ? ' (required)' : ' (optional, omitted = null)'}`).join(', ')}</p>
      <label>Named input values (JSON object)<textarea rows={5} value={runInputs} onChange={event => setRunInputs(event.target.value)}/></label><details><summary>Tool schemas for manual testing</summary><label>Function tools (JSON array)<textarea rows={5} value={tools} onChange={event => setTools(event.target.value)}/></label><p>Hermes supplies these schemas in real runs. The UI only accepts manual results.</p></details>
      <button disabled={busy || dirty} onClick={() => action(async () => { const response = await client.json<StartRunResponse>('/api/runs', { method: 'POST', body: JSON.stringify({ graph_id: graph.id, revision: graph.revision, inputs: JSON.parse(runInputs), tools: JSON.parse(tools), messages: [] }) }); setActiveRun(response.run_id); setNotice('Run started.'); })}>Start test run</button>{activeRun && <RunDetail client={client} runId={activeRun}/>}</section>
    </> : <div className="empty"><h2>Create or open a graph</h2><p>Connect to load installed models and saved graphs.</p></div>}</main></div> : <main className="history-page"><History client={client} refreshKey={refreshKey} onOpen={setActiveRun}/>{activeRun && <RunDetail client={client} runId={activeRun}/>}</main>}
  </div>;
}
