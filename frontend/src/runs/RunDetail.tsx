import { useEffect, useState } from 'react';
import { ApiClient } from '../api/client';
import type { RunDetailResponse, ToolResultsResponse } from '../contracts/generated';
const terminal = new Set(['completed', 'failed', 'cancelled', 'interrupted']);
export function RunDetail({ client, runId }: {
    client: ApiClient;
    runId: string;
}) {
    const [detail, setDetail] = useState<RunDetailResponse | null>(null), [error, setError] = useState('');
    const [results, setResults] = useState<Record<string, string>>({}), [selected, setSelected] = useState<string[]>([]);
    const [refresh, setRefresh] = useState(0), [busy, setBusy] = useState(false);
    useEffect(() => {
        const controller = new AbortController();
        setDetail(null);
        setError('');
        setResults({});
        setSelected([]);
        const reload = async () => { const value = await client.json<RunDetailResponse>(`/api/runs/${encodeURIComponent(runId)}`, { signal: controller.signal }); if (!controller.signal.aborted)
            setDetail(value); return value; };
        reload().then(async (value) => { if (!terminal.has(value.run.status))
            await client.events(runId, controller.signal, async () => { await reload(); }); }).catch(error => { if (!controller.signal.aborted)
            setError(error.message); });
        return () => controller.abort();
    }, [client, runId, refresh]);
    async function cancel() { setBusy(true); setError(''); try {
        await client.json(`/api/runs/${encodeURIComponent(runId)}/cancel`, { method: 'POST' });
        setRefresh(value => value + 1);
    }
    catch (error) {
        setError((error as Error).message);
    }
    finally {
        setBusy(false);
    } }
    async function submit() {
        setBusy(true);
        setError('');
        try {
            const response = await client.json<ToolResultsResponse>(`/api/runs/${encodeURIComponent(runId)}/tool-results`, { method: 'POST', body: JSON.stringify({ results: selected.map(id => ({ tool_call_id: id, content: results[id] ?? '' })) }) });
            setSelected(ids => ids.filter(id => !response.accepted_ids.includes(id)));
            setRefresh(value => value + 1);
        }
        catch (error) {
            setError((error as Error).message);
        }
        finally {
            setBusy(false);
        }
    }
    return <section className="run-detail"><div className="row"><h2>Run details</h2><button onClick={() => setRefresh(value => value + 1)}>Refresh run</button><button disabled={!detail || terminal.has(detail.run.status) || busy} onClick={cancel}>Cancel run</button></div>
    <code className="break">{runId}</code>{error && <p role="alert">{error}</p>}
    {detail && <><p><strong data-testid="run-status">{detail.run.status}</strong> · {detail.run.graph_id} · revision {detail.run.revision}</p>
      <dl><dt>Snapshot hash</dt><dd className="break">{detail.run.graph_hash}</dd><dt>Started</dt><dd>{detail.run.started_at ?? 'Not started'}</dd><dt>Ended</dt><dd>{detail.run.ended_at ?? '—'}</dd><dt>Active duration</dt><dd>{detail.run.duration_seconds.toFixed(2)}s · queued {detail.run.queue_seconds.toFixed(2)}s</dd><dt>Executions / attempts / tool batches</dt><dd>{detail.run.node_executions} / {detail.run.upstream_attempts} / {detail.run.tool_rounds}</dd></dl>
      {detail.error && <p role="alert">{detail.error.code}: {detail.error.message}</p>}
      {detail.run.status === 'completed' && <div><h3>Final output</h3><pre data-testid="run-output">{JSON.stringify(detail.output, null, 2)}</pre></div>}
      <h3>Node activations</h3>{detail.activations.length === 0 && <p>No activations yet.</p>}
      {detail.activations.map(activation => <article className="activation" key={activation.activation_id}><h4>{activation.node_id} · {activation.scope_key || 'outside loops'} · iteration {activation.iteration}</h4>
        <p>{activation.status} · Ready ports: {activation.ready_ports.join(', ') || 'none'} / Expected ports: {activation.expected_ports.join(', ') || 'none'}</p>
        <small>{activation.started_at ?? 'Not started'} → {activation.ended_at ?? '—'}</small>
        {activation.error && <p role="alert">{activation.error.code}: {activation.error.message}</p>}
        {'payload' in activation && <pre>{JSON.stringify(activation.payload, null, 2)}</pre>}
        {activation.usage && <p>Upstream tokens: {activation.usage.prompt_tokens} input + {activation.usage.completion_tokens} output = {activation.usage.total_tokens}</p>}
      </article>)}
      {detail.pending_tools.length > 0 && <><h3>Tool results</h3><p>The UI does not execute tools. Enter results manually, or execute this graph through Hermes. The displayed tool-wait deadline is fixed for the batch and does not extend after partial results. Tool waiting has a separate TTL and is excluded from active execution time.</p>
        {detail.pending_tools.map(tool => <article className="activation" key={tool.tool_call_id}><h4>{tool.name} · {tool.node_id}</h4><code className="break">{tool.tool_call_id}</code><pre>{tool.arguments}</pre><p>{tool.status} · expires {tool.expires_at}</p>
          {tool.status === 'pending' && !terminal.has(detail.run.status) ? <><label><input type="checkbox" checked={selected.includes(tool.tool_call_id)} onChange={event => setSelected(event.target.checked ? [...selected, tool.tool_call_id] : selected.filter(id => id !== tool.tool_call_id))}/>Submit this result</label><label>Result for {tool.tool_call_id}<textarea value={results[tool.tool_call_id] ?? ''} onChange={event => setResults({ ...results, [tool.tool_call_id]: event.target.value })}/></label></> : <pre>{tool.result}</pre>}
        </article>)}<button disabled={selected.length === 0 || busy || terminal.has(detail.run.status)} onClick={submit}>Submit selected results</button></>}
      <details><summary>Immutable run graph</summary><pre>{JSON.stringify(detail.snapshot, null, 2)}</pre></details>
    </>}
  </section>;
}
