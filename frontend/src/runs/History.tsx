import { useEffect, useState } from 'react';
import { ApiClient } from '../api/client';
import type { RunListResponse, RunSummary } from '../contracts/generated';
interface Props {
    client: ApiClient;
    onOpen: (id: string) => void;
    refreshKey: number;
}
export function History({ client, onOpen, refreshKey }: Props) {
    const [graph, setGraph] = useState(''), [status, setStatus] = useState(''), [offset, setOffset] = useState(0);
    const [page, setPage] = useState<RunListResponse | null>(null), [error, setError] = useState('');
    const [reload, setReload] = useState(0);
    useEffect(() => {
        const controller = new AbortController();
        setError('');
        const params = new URLSearchParams({ limit: '20', offset: String(offset) });
        if (graph)
            params.set('graph_id', graph);
        if (status)
            params.set('status', status);
        client.json<RunListResponse>(`/api/runs?${params}`, { signal: controller.signal }).then(setPage).catch(error => { if (!controller.signal.aborted)
            setError(error.message); });
        return () => controller.abort();
    }, [client, graph, status, offset, reload, refreshKey]);
    return <section className="history"><div className="row"><h2>Run history</h2><button onClick={() => setReload(value => value + 1)}>Refresh history</button></div>
    <div className="row"><label>Graph filter<input value={graph} onChange={event => { setGraph(event.target.value); setOffset(0); }}/></label>
      <label>Status filter<select value={status} onChange={event => { setStatus(event.target.value); setOffset(0); }}><option value="">All statuses</option>{(['queued', 'running', 'waiting_tools', 'completed', 'failed', 'cancelled', 'interrupted'] as RunSummary['status'][]).map(state => <option key={state}>{state}</option>)}</select></label></div>
    {error && <p role="alert">{error}</p>}
    <div className="table-scroll"><table><thead><tr><th>Run / graph</th><th>Status</th><th>Revision / hash</th><th>Start</th><th>End</th><th>Duration</th></tr></thead><tbody>
      {page?.runs.map(run => <tr key={run.run_id}><td><button className="link" onClick={() => onOpen(run.run_id)}>{run.run_id}</button><br />{run.graph_id}</td><td>{run.status}</td><td>{run.revision}<br /><code title={run.graph_hash}>{run.graph_hash.slice(0, 12)}</code></td><td>{run.started_at ?? run.created_at}</td><td>{run.ended_at ?? '—'}</td><td>{run.duration_seconds.toFixed(2)}s<br /><small>Queue: {run.queue_seconds.toFixed(2)}s</small></td></tr>)}
    </tbody></table></div>
    {page?.runs.length === 0 && <p>No runs match these filters.</p>}
    <div className="row"><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 20))}>Previous page</button><span>{page ? `${offset + 1 > page.total ? page.total : offset + 1}–${Math.min(offset + 20, page.total)} of ${page.total}` : 'Loading…'}</span><button disabled={!page || offset + 20 >= page.total} onClick={() => setOffset(offset + 20)}>Next page</button></div>
  </section>;
}
