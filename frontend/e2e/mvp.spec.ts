import { test, expect, type Page } from '@playwright/test';
import { createServer, type Server } from 'node:http';
import { createServer as createPortProbe } from 'node:net';
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Graph } from '../src/contracts/generated';
// This fixture exercises the production API and SQLite; only Ollama is simulated.
// Temporary data is retained for inspection. Existing API listeners are never reused.
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const token = 'cg-ui-e2e-local-token';
const auth = { Authorization: `Bearer ${token}` };
let upstream: Server, backend: ChildProcess, dataDir = '', endpoint = '', logs = '', upstreamCalls = 0;
let controllerRounds = 0;
const sleep = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms));
async function stopBackend() {
    if (!backend || backend.exitCode !== null || backend.signalCode !== null)
        return;
    // Windows venv redirectors create a Python child; stop only this owned process tree.
    if (process.platform === 'win32' && backend.pid)
        execFileSync('taskkill', ['/PID', String(backend.pid), '/T', '/F'], { windowsHide: true, stdio: 'pipe' });
    else
        backend.kill('SIGTERM');
    for (let count = 0; count < 60 && backend.exitCode === null && backend.signalCode === null; count++)
        await sleep(100);
    if (backend.exitCode === null && backend.signalCode === null)
        throw new Error(`UI test backend PID ${backend.pid} did not stop; preserve its temporary data.`);
    console.log(`UI owned backend process tree stopped: PID ${backend.pid}`);
}
async function startBackend() {
    logs = '';
    const python = execFileSync('uv', ['--system-certs', 'run', '--project', 'backend', '--locked', 'python', '-c', 'import sys; print(sys.executable)'], { cwd: root, encoding: 'utf8', windowsHide: true }).trim();
    backend = spawn(python, ['-m', 'uvicorn', 'app.main:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', '8000', '--workers', '1', '--no-access-log'], {
        cwd: root, env: { ...process.env, CG_DATA_DIR: dataDir, CG_API_TOKEN: token, OLLAMA_BASE_URL: endpoint, CG_MAX_PARALLEL_LLM: '2', CG_MAX_ACTIVE_RUNS: '4', CG_MAX_QUEUED_RUNS: '20' }, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'],
    });
    backend.stdout?.on('data', chunk => { logs += String(chunk); });
    backend.stderr?.on('data', chunk => { logs += String(chunk); });
    let spawnError: Error | undefined;
    backend.on('error', error => { spawnError = error; });
    for (let count = 0; count < 100; count++) {
        if (spawnError)
            throw new Error(`Pinned uv/backend prerequisite unavailable: ${spawnError.message}`);
        if (backend.exitCode !== null)
            throw new Error(`Production backend failed to launch (${backend.exitCode}): ${logs}`);
        try {
            const response = await fetch('http://127.0.0.1:8000/health/ready');
            if (response.status === 404)
                throw new Error('Production backend /health/ready prerequisite unavailable. Complete API composition before UI acceptance.');
            if (response.ok) {
                const ready = await response.json();
                if (ready.storage_ready && logs.includes('Uvicorn running')) {
                    console.log(`UI production backend ready: PID ${backend.pid}, data ${dataDir}`);
                    return;
                }
            }
        }
        catch (error) {
            if (error instanceof Error && error.message.startsWith('Production backend'))
                throw error;
        }
        await sleep(100);
    }
    throw new Error(`Production backend /health/ready prerequisite unavailable. Complete API composition before UI acceptance. ${logs}`);
}
test.beforeAll(async () => {
    await new Promise<void>((resolve, reject) => {
        const probe = createPortProbe();
        probe.once('error', () => reject(new Error('Port 8000 is already in use or unavailable; stop the known local API before running the isolated UI fixture.')));
        probe.listen(8000, '127.0.0.1', () => probe.close(() => resolve()));
    });
    dataDir = await mkdtemp(resolve(tmpdir(), 'cg-ui-e2e-'));
    console.log(`UI acceptance retained data: ${dataDir}`);
    upstream = createServer(async (request, response) => {
        response.setHeader('Content-Type', 'application/json');
        if (request.url === '/v1/models') {
            response.end(JSON.stringify({ object: 'list', data: [{ id: 'ui-fixture', object: 'model', created: 0, owned_by: 'ollama' }] }));
            return;
        }
        if (request.url !== '/v1/chat/completions') {
            response.statusCode = 404;
            response.end('{}');
            return;
        }
        let raw = '';
        for await (const chunk of request)
            raw += String(chunk);
        const body = JSON.parse(raw);
        upstreamCalls++;
        const messages = body.messages as Array<{
            role: string;
            content?: string;
        }>;
        const usesTools = messages.some(message => message.role === 'system' && message.content?.includes('tool-fixture'));
        const toolResult = messages.some(message => message.role === 'tool');
        if (messages.some(message => message.content?.includes('slow-fixture')))
            await sleep(1600);
        const controllerSchema = body.response_format?.json_schema?.schema;
        const isController = controllerSchema?.properties?.control && controllerSchema?.properties?.payload;
        const iteration = controllerRounds;
        const decisions = controllerSchema?.$defs?.Control?.properties?.decision?.enum ?? ['again', 'done'];
        if (isController) controllerRounds++;
        const content = isController ? JSON.stringify({ payload: `Loop payload ${iteration}`, control: { decision: iteration < 2 ? decisions[0] : decisions[1] } }) : toolResult ? 'Owner received manual result' : 'Fixture final output';
        const message = usesTools && !toolResult ? { role: 'assistant', content: null, tool_calls: [{ id: 'internal-collision', type: 'function', function: { name: 'fixture_read', arguments: '{"path":"fixture.txt"}' } }] } : { role: 'assistant', content };
        response.end(JSON.stringify({ id: `chatcmpl-ui-${upstreamCalls}`, object: 'chat.completion', created: 0, model: 'ui-fixture', choices: [{ index: 0, message, finish_reason: usesTools && !toolResult ? 'tool_calls' : 'stop' }], usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 } }));
    });
    await new Promise<void>(resolve => upstream.listen(0, '127.0.0.1', resolve));
    const address = upstream.address();
    if (!address || typeof address === 'string')
        throw new Error('Mock upstream did not bind.');
    endpoint = `http://127.0.0.1:${address.port}/v1`;
    await startBackend();
});
test.afterAll(async () => { await stopBackend(); if (upstream)
    await new Promise<void>(resolve => upstream.close(() => resolve())); });
async function connectPage(page: Page) { await page.goto('/'); await page.getByLabel('API token', { exact: true }).fill(token); await page.getByRole('button', { name: 'Connect / refresh' }).click(); await expect(page.getByLabel('Installed model')).toContainText('ui-fixture'); }
async function exported(page: Page): Promise<Graph> { const download = page.waitForEvent('download'); await page.getByRole('button', { name: 'Export graph', exact: true }).click(); const item = await download; const path = await item.path(); if (!path)
    throw new Error('Export download missing'); return JSON.parse(await readFile(path, 'utf8')); }
async function importNew(page: Page, value: Graph) {
    const panel = page.locator('.graph-list details');
    const json = panel.locator('textarea');
    if (await panel.getAttribute('open') === null) await panel.locator('summary').click();
    await expect(json).toBeVisible();
    await json.fill(JSON.stringify(value));
    await page.getByRole('button', { name: 'Import graph', exact: true }).click();
    await expect(page.locator('.toolbar')).toContainText(value.name);
}
function passThrough(id: string): Graph { return { schema_version: 1, id, name: id, revision: 1, base_model: 'ui-fixture', inputs: [{ id: 'chat', required: true }, { id: 'optional', required: false }], nodes: [{ id: 'input', type: 'input', input_id: 'chat', position: { x: 0, y: 80 } }, { id: 'output', type: 'output', position: { x: 300, y: 80 } }], edges: [{ id: 'answer', source: 'input', target: 'output', target_port: 'answer', kind: 'forward' }], loops: [], output_node_id: 'output' }; }
test('create, prompt/ports/feedback, publication, import/export and API reload', async ({ page, request }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await connectPage(page);
    await page.getByLabel('Graph ID', { exact: true }).fill('ui-editor');
    await page.getByLabel('Graph name', { exact: true }).fill('UI editor graph');
    await page.getByRole('button', { name: 'Create graph', exact: true }).click();
    await page.locator('.react-flow__node[data-id="think"]').click();
    await page.getByLabel('System prompt').fill('Changed prompt');
    await page.getByLabel('Tools enabled').check();
    await page.getByLabel('Generation settings (JSON)').fill('{"temperature":0.3}');
    await page.getByRole('button', { name: 'Apply generation settings' }).click();
    await page.getByLabel('Scope ID').fill('refine');
    await page.getByRole('group', { name: 'Scope members' }).getByLabel('think', { exact: true }).check();
    await page.getByLabel('Controller', { exact: true }).selectOption('think');
    await page.getByLabel('Continue value').fill('again');
    await page.getByLabel('Exit value').fill('done');
    await page.getByRole('button', { name: 'Apply loop scope' }).click();
    await page.getByLabel('Source', { exact: true }).selectOption('think');
    await page.getByLabel('Target', { exact: true }).selectOption('think');
    await page.getByLabel('Target port').fill('previous');
    await page.getByLabel('Connection kind').selectOption('feedback');
    await page.getByLabel('Loop scope', { exact: true }).selectOption('refine');
    await page.getByLabel('Feedback seed (JSON, including null)').fill('null');
    await page.getByRole('button', { name: 'Add connection', exact: true }).click();
    await expect(page.locator('.react-flow__node[data-id="think"] .react-flow__handle[data-handleid="previous"]')).toBeVisible();
    await expect(page.locator('.react-flow__edge')).toHaveCount(3);
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await expect(page.locator('.toolbar')).toContainText('revision 2');
    await page.getByRole('button', { name: 'Publish revision' }).click();
    await expect(page.getByRole('status').filter({ hasText: 'Published cg/ui-editor' })).toBeVisible();
    const value = await exported(page);
    expect(value.loops[0]).toMatchObject({ continue_value: 'again', exit_value: 'done' });
    expect(value.edges.find(edge => edge.kind === 'feedback')).toHaveProperty('initial_value', null);
    expect(JSON.stringify(value)).not.toContain(token);
    await page.getByLabel('Named input values (JSON object)').fill('{"chat":"Show seeded loop iterations"}');
    await page.getByRole('button', { name: 'Start test run' }).click();
    await expect(page.getByTestId('run-status')).toHaveText('completed');
    await expect(page.getByTestId('run-output')).toContainText('Loop payload 2');
    for (const iteration of [0, 1, 2]) {
        await expect(page.getByRole('heading', { name: `think · refine · iteration ${iteration}`, exact: true })).toBeVisible();
    }
    await request.put('http://127.0.0.1:8000/api/graphs/ui-editor', { headers: auth, data: { graph: { ...value, name: 'Concurrent update' }, expected_revision: value.revision } });
    await page.getByLabel('Name', { exact: true }).fill('Local retained edit');
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await expect(page.getByRole('alert')).toContainText('revision');
    await expect(page.getByLabel('Name', { exact: true })).toHaveValue('Local retained edit');
    await page.getByRole('button', { name: 'Reload server version' }).click();
    await expect(page.getByLabel('Name', { exact: true })).toHaveValue('Concurrent update');
    await importNew(page, { ...value, id: 'ui-copy', name: 'Imported copy' });
    await expect(page.locator('.toolbar')).toContainText('revision 1');
    await page.reload();
    await expect(page.getByLabel('API token', { exact: true })).toHaveValue('');
    await page.getByLabel('API token', { exact: true }).fill(token);
    await page.getByRole('button', { name: 'Connect / refresh' }).click();
    await page.getByRole('button', { name: /Imported copy ui-copy/ }).click();
    expect((await exported(page)).edges).toEqual(value.edges);
    expect(errors).toEqual([]);
});
test('named inputs, immutable snapshot, history, draft visibility and process persistence', async ({ page, request }) => {
    await connectPage(page);
    const graph = passThrough('ui-run');
    await importNew(page, graph);
    const before = upstreamCalls;
    await page.getByLabel('Named input values (JSON object)').fill('{}');
    await page.getByRole('button', { name: 'Start test run' }).click();
    await expect(page.getByRole('alert')).toBeVisible();
    expect(upstreamCalls).toBe(before);
    await page.getByLabel('Named input values (JSON object)').fill('{"chat":"Persisted answer"}');
    await page.getByRole('button', { name: 'Start test run' }).click();
    await expect(page.getByTestId('run-status')).toHaveText('completed');
    await expect(page.getByTestId('run-output')).toContainText('Persisted answer');
    const runId = await page.locator('.run-detail>code').textContent();
    expect(runId).toBeTruthy();
    const response = await request.get('http://127.0.0.1:8000/v1/models', { headers: auth });
    expect((await response.json()).data.some((item: {
        id: string;
    }) => item.id === 'cg/ui-run')).toBe(false);
    await page.getByLabel('Name', { exact: true }).fill('Later draft');
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await expect(page.locator('.toolbar')).toContainText('revision 2');
    await stopBackend();
    await startBackend();
    await page.reload();
    await page.getByLabel('API token', { exact: true }).fill(token);
    await page.getByRole('button', { name: 'Connect / refresh' }).click();
    await page.getByRole('button', { name: 'History', exact: true }).click();
    await page.getByLabel('Graph filter').fill('ui-run');
    await page.getByRole('button', { name: runId!, exact: true }).click();
    await expect(page.getByTestId('run-status')).toHaveText('completed');
    await expect(page.getByTestId('run-output')).toContainText('Persisted answer');
    await expect(page.locator('.run-detail')).toContainText('revision 1');
});
test('tool wait survives restart and manual result resumes its owner', async ({ page, request }) => {
    await connectPage(page);
    await page.getByLabel('Graph ID', { exact: true }).fill('ui-tools');
    await page.getByLabel('Graph name', { exact: true }).fill('UI manual tools');
    await page.getByRole('button', { name: 'Create graph', exact: true }).click();
    await page.locator('.react-flow__node[data-id="think"]').click();
    await page.getByLabel('System prompt').fill('tool-fixture');
    await page.getByLabel('Tools enabled').check();
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await page.getByText('Tool schemas for manual testing', { exact: true }).click();
    await page.getByLabel('Function tools (JSON array)').fill('[{"type":"function","function":{"name":"fixture_read","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}}]');
    await page.getByLabel('Named input values (JSON object)').fill('{"chat":"Read the fixture"}');
    await page.getByRole('button', { name: 'Start test run' }).click();
    await expect(page.getByTestId('run-status')).toHaveText('waiting_tools');
    const id = await page.locator('.run-detail>code').textContent();
    const detail = await (await request.get(`http://127.0.0.1:8000/api/runs/${id}`, { headers: auth })).json();
    const pendingId = detail.pending_tools[0].tool_call_id;
    await stopBackend();
    await startBackend();
    await page.getByRole('button', { name: 'Refresh run' }).click();
    await expect(page.getByTestId('run-status')).toHaveText('waiting_tools');
    await expect(page.locator('.run-detail')).toContainText(pendingId);
    await page.getByLabel('Submit this result').check();
    await page.getByLabel(`Result for ${pendingId}`, { exact: true }).fill('Manual fixture contents');
    await page.getByRole('button', { name: 'Submit selected results' }).click();
    await expect(page.getByTestId('run-status')).toHaveText('completed');
    await expect(page.getByTestId('run-output')).toContainText('Owner received manual result');
});
test('editing an active run preserves its snapshot and cancellation is explicit', async ({ page, request }) => {
    await connectPage(page);
    await page.getByLabel('Graph ID', { exact: true }).fill('ui-active');
    await page.getByLabel('Graph name', { exact: true }).fill('Active original');
    await page.getByRole('button', { name: 'Create graph', exact: true }).click();
    await page.locator('.react-flow__node[data-id="think"]').click();
    await page.getByLabel('System prompt').fill('slow-fixture');
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await page.getByLabel('Named input values (JSON object)').fill('{"chat":"Snapshot question"}');
    await page.getByRole('button', { name: 'Start test run' }).click();
    await expect(page.getByTestId('run-status')).toHaveText('running');
    const id = await page.locator('.run-detail>code').textContent();
    await page.getByLabel('Name', { exact: true }).fill('Edited while running');
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    const detail = await (await request.get(`http://127.0.0.1:8000/api/runs/${id}`, { headers: auth })).json();
    expect(detail.snapshot.name).toBe('Active original');
    expect(detail.run.revision).toBe(2);
    await expect(page.getByTestId('run-status')).toHaveText('completed');
    await page.getByLabel('Named input values (JSON object)').fill('{"chat":"Cancel this run"}');
    await page.getByRole('button', { name: 'Start test run' }).click();
    await expect(page.getByTestId('run-status')).toHaveText('running');
    await page.getByRole('button', { name: 'Cancel run', exact: true }).click();
    await expect(page.getByTestId('run-status')).toHaveText('cancelled');
});
test('same-ID API reload displays and applies current generation without stale overwrite', async ({ page, request }) => {
    await connectPage(page);
    await page.getByLabel('Graph ID', { exact: true }).fill('ui-reload-generation');
    await page.getByLabel('Graph name', { exact: true }).fill('Reload generation');
    await page.getByRole('button', { name: 'Create graph', exact: true }).click();
    await page.locator('.react-flow__node[data-id="think"]').click();
    const original = await exported(page);
    const updated: Graph = { ...original, nodes: original.nodes.map(node => node.type === 'llm' ? { ...node, generation: { temperature: 0.7 } } : node) };
    const saved = await request.put('http://127.0.0.1:8000/api/graphs/ui-reload-generation', { headers: auth, data: { graph: updated, expected_revision: original.revision } });
    expect(saved.ok()).toBe(true);
    await page.getByRole('button', { name: /Reload generation ui-reload-generation/ }).click();
    await expect(page.locator('.toolbar')).toContainText('revision 2');
    const loaded = await exported(page);
    const displayed = JSON.parse(await page.getByLabel('Generation settings (JSON)').inputValue());
    await page.getByRole('button', { name: 'Apply generation settings' }).click();
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await expect(page.locator('.toolbar')).toContainText('revision 3');
    const persisted: Graph = await (await request.get('http://127.0.0.1:8000/api/graphs/ui-reload-generation', { headers: auth })).json();
    expect(loaded.nodes.find(node => node.type === 'llm')).toMatchObject({ generation: { temperature: 0.7 } });
    expect(displayed.temperature).toBe(0.7);
    expect(persisted.nodes.find(node => node.type === 'llm')).toMatchObject({ generation: { temperature: 0.7 } });
});
test('reload and same-ID import rebase edge and scope inspectors while local drafts survive edits', async ({ page, request }) => {
    const graph: Graph = {
        schema_version: 1, id: 'ui-reload-inspectors', name: 'Inspector reload', revision: 1, base_model: 'ui-fixture',
        inputs: [{ id: 'chat', required: true }],
        nodes: [
            { id: 'input', type: 'input', input_id: 'chat', position: { x: 0, y: 80 } },
            { id: 'think', type: 'llm', system_prompt: 'Draft', tools_enabled: false, generation: { temperature: 0.2 }, position: { x: 240, y: 80 } },
            { id: 'critic', type: 'llm', system_prompt: 'Critique', tools_enabled: false, generation: {}, position: { x: 480, y: 80 } },
            { id: 'output', type: 'output', position: { x: 720, y: 80 } },
        ],
        edges: [
            { id: 'question', source: 'input', target: 'think', target_port: 'question', kind: 'forward' },
            { id: 'draft', source: 'think', target: 'critic', target_port: 'draft', kind: 'forward' },
            { id: 'answer', source: 'critic', target: 'output', target_port: 'answer', kind: 'forward' },
            { id: 'feedback', source: 'critic', target: 'think', target_port: 'previous', kind: 'feedback', loop_id: 'refine', initial_value: 'original' },
        ],
        loops: [{ id: 'refine', node_ids: ['think', 'critic'], controller_node_id: 'critic', continue_value: 'again', exit_value: 'done' }],
        output_node_id: 'output',
    };
    expect((await request.post('http://127.0.0.1:8000/api/graphs', { headers: auth, data: graph })).ok()).toBe(true);
    await connectPage(page);
    await page.getByRole('button', { name: /Inspector reload ui-reload-inspectors/ }).click();
    await page.locator('.react-flow__node[data-id="think"]').click();
    const generation = page.getByLabel('Generation settings (JSON)');
    await generation.fill('{"temperature":0.6}');
    await page.locator('.react-flow__node[data-id="critic"]').click();
    await page.locator('.react-flow__node[data-id="think"]').click();
    await expect(generation).toHaveValue('{"temperature":0.6}');
    await page.getByLabel('System prompt').fill('Edited prompt');
    await page.getByLabel('Source', { exact: true }).selectOption('input');
    await page.getByLabel('Target', { exact: true }).selectOption('think');
    await page.getByLabel('Target port').fill('context');
    await page.getByRole('button', { name: 'Add connection', exact: true }).click();
    await expect(page.locator('.react-flow__node[data-id="think"] .react-flow__handle[data-handleid="context"]')).toBeVisible();
    await expect(generation).toHaveValue('{"temperature":0.6}');
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await expect(page.locator('.toolbar')).toContainText('revision 2');
    await expect(generation).toHaveValue('{"temperature":0.6}');
    const current: Graph = await (await request.get('http://127.0.0.1:8000/api/graphs/ui-reload-inspectors', { headers: auth })).json();
    expect(current.nodes.find(node => node.id === 'think')).toMatchObject({ generation: { temperature: 0.2 } });
    const selectFeedback = async () => {
        await page.locator('.react-flow__edge[data-id="feedback"] .react-flow__edge-interaction').click({ force: true });
        await page.getByRole('button', { name: 'refine', exact: true }).click();
    };
    await selectFeedback();
    await page.getByLabel('Feedback seed (JSON, including null)').fill('"unsaved seed"');
    await page.getByLabel('Exit value').fill('unsaved exit');
    const server: Graph = {
        ...current,
        nodes: current.nodes.map(node => node.id === 'think' && node.type === 'llm' ? { ...node, generation: { temperature: 0.7 } } : node),
        edges: current.edges.map(edge => edge.kind === 'feedback' ? { ...edge, target_port: 'server_previous', initial_value: 'server seed' } : edge),
        loops: current.loops.map(loop => ({ ...loop, continue_value: 'go', exit_value: 'finish' })),
    };
    expect((await request.put('http://127.0.0.1:8000/api/graphs/ui-reload-inspectors', { headers: auth, data: { graph: server, expected_revision: current.revision } })).ok()).toBe(true);
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await expect(page.getByRole('alert')).toContainText('revision');
    await expect(generation).toHaveValue('{"temperature":0.6}');
    await expect(page.getByLabel('Feedback seed (JSON, including null)')).toHaveValue('"unsaved seed"');
    await page.getByRole('button', { name: 'Reload server version' }).click();
    await expect(page.locator('.toolbar')).toContainText('revision 3');
    expect(JSON.parse(await generation.inputValue()).temperature).toBe(0.7);
    await expect(page.getByLabel('Target port')).toHaveValue('server_previous');
    await expect(page.getByLabel('Feedback seed (JSON, including null)')).toHaveValue('"server seed"');
    await expect(page.getByLabel('Continue value')).toHaveValue('go');
    await expect(page.getByLabel('Exit value')).toHaveValue('finish');
    await page.getByRole('button', { name: 'Apply generation settings' }).click();
    await page.getByRole('button', { name: 'Apply connection', exact: true }).click();
    await page.getByRole('button', { name: 'Apply loop scope' }).click();
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await expect(page.locator('.toolbar')).toContainText('revision 4');
    const saved: Graph = await (await request.get('http://127.0.0.1:8000/api/graphs/ui-reload-inspectors', { headers: auth })).json();
    expect(saved.edges.find(edge => edge.id === 'feedback')).toMatchObject({ target_port: 'server_previous', initial_value: 'server seed' });
    expect(saved.loops[0]).toMatchObject({ continue_value: 'go', exit_value: 'finish' });
    await selectFeedback();
    const imported: Graph = {
        ...saved, name: 'Inspector imported',
        nodes: saved.nodes.map(node => node.id === 'think' && node.type === 'llm' ? { ...node, generation: { temperature: 0.9 } } : node),
        edges: saved.edges.map(edge => edge.kind === 'feedback' ? { ...edge, target_port: 'import_previous', initial_value: 'import seed' } : edge),
        loops: saved.loops.map(loop => ({ ...loop, continue_value: 'import_again', exit_value: 'import_done' })),
    };
    await importNew(page, imported);
    expect(JSON.parse(await generation.inputValue()).temperature).toBe(0.9);
    await expect(page.getByLabel('Target port')).toHaveValue('import_previous');
    await expect(page.getByLabel('Feedback seed (JSON, including null)')).toHaveValue('"import seed"');
    await expect(page.getByLabel('Continue value')).toHaveValue('import_again');
    await expect(page.getByLabel('Exit value')).toHaveValue('import_done');
    await page.getByRole('button', { name: 'Apply generation settings' }).click();
    await page.getByRole('button', { name: 'Apply connection', exact: true }).click();
    await page.getByRole('button', { name: 'Apply loop scope' }).click();
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await expect(page.locator('.toolbar')).toContainText('revision 5');
    const importedSaved: Graph = await (await request.get('http://127.0.0.1:8000/api/graphs/ui-reload-inspectors', { headers: auth })).json();
    expect(importedSaved.nodes.find(node => node.id === 'think')).toMatchObject({ generation: { temperature: 0.9 } });
    expect(importedSaved.edges.find(edge => edge.id === 'feedback')).toMatchObject({ target_port: 'import_previous', initial_value: 'import seed' });
    expect(importedSaved.loops[0].exit_value).toBe('import_done');
    await selectFeedback();
    await importNew(page, { ...importedSaved, loops: [], edges: importedSaved.edges.filter(edge => edge.kind !== 'feedback') });
    await expect(page.getByLabel('Target port')).toHaveValue('');
    await expect(page.getByLabel('Source', { exact: true })).toHaveValue('');
    await expect(page.getByLabel('Scope ID')).toHaveValue('');
    await expect(page.getByLabel('Controller', { exact: true })).toHaveValue('');
    await expect(page.getByLabel('Continue value')).toHaveValue('continue');
    await expect(page.getByLabel('Exit value')).toHaveValue('stop');
    await expect(page.getByRole('button', { name: 'Apply connection', exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'Save graph', exact: true }).click();
    await expect(page.locator('.toolbar')).toContainText('revision 6');
    const cleared: Graph = await (await request.get('http://127.0.0.1:8000/api/graphs/ui-reload-inspectors', { headers: auth })).json();
    expect(cleared.loops).toEqual([]);
    expect(cleared.edges.every(edge => edge.kind !== 'feedback')).toBe(true);
});
