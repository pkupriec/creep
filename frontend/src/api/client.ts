import type { RunEvent } from '../contracts/generated';
export class ApiError extends Error {
    constructor(public status: number, public code: string, message: string) { super(message); }
}
export interface SSEMessage {
    id: string;
    event: string;
    data: string;
}
/** Decode complete SSE frames only; an interrupted frame is never acknowledged. */
export async function* parseSSE(body: ReadableStream<Uint8Array>): AsyncGenerator<SSEMessage> {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    try {
        while (true) {
            const { value, done } = await reader.read();
            buffer += decoder.decode(value, { stream: !done });
            if (buffer.length > 2 * 1024 * 1024)
                throw new ApiError(502, 'invalid_event', 'Event exceeds the size limit.');
            let boundary: RegExpExecArray | null;
            while ((boundary = /\r?\n\r?\n/.exec(buffer))) {
                const frame = buffer.slice(0, boundary.index);
                buffer = buffer.slice(boundary.index + boundary[0].length);
                let id = '', event = 'message';
                const data: string[] = [];
                for (const line of frame.split(/\r?\n/)) {
                    if (line.startsWith(':'))
                        continue;
                    const colon = line.indexOf(':');
                    const name = colon < 0 ? line : line.slice(0, colon);
                    const text = colon < 0 ? '' : line.slice(colon + 1).replace(/^ /, '');
                    if (name === 'id' && !text.includes('\0'))
                        id = text;
                    if (name === 'event')
                        event = text;
                    if (name === 'data')
                        data.push(text);
                }
                if (data.length)
                    yield { id, event, data: data.join('\n') };
            }
            if (done)
                break;
        }
    }
    finally {
        await reader.cancel().catch(() => { });
        reader.releaseLock();
    }
}
function pause(ms: number, signal: AbortSignal): Promise<void> {
    return new Promise((resolve, reject) => {
        if (signal.aborted) {
            reject(signal.reason);
            return;
        }
        const abort = () => { clearTimeout(timer); reject(signal.reason); };
        const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, ms);
        signal.addEventListener('abort', abort, { once: true });
    });
}
export class ApiClient {
    constructor(private token: () => string, private fetcher: typeof fetch = fetch, private wait = pause) { }
    private headers(init?: HeadersInit): Headers {
        const headers = new Headers(init);
        if (this.token())
            headers.set('Authorization', `Bearer ${this.token()}`);
        return headers;
    }
    private async failure(response: Response): Promise<never> {
        let message = `Request failed (${response.status}).`, code = 'request_failed';
        try {
            const payload = await response.json();
            if (typeof payload.error?.message === 'string')
                message = payload.error.message;
            if (typeof payload.error?.code === 'string')
                code = payload.error.code;
        }
        catch { /* Non-JSON transport failures retain a safe description. */ }
        throw new ApiError(response.status, code, message);
    }
    async json<T>(path: string, init: RequestInit = {}): Promise<T> {
        const headers = this.headers(init.headers);
        if (init.body)
            headers.set('Content-Type', 'application/json');
        const response = await this.fetcher.call(globalThis, path, { ...init, headers });
        if (!response.ok)
            return this.failure(response);
        return response.json() as Promise<T>;
    }
    /** Only the read-only event subscription reconnects. Mutations are never retried. */
    async events(runId: string, signal: AbortSignal, onEvent: (event: RunEvent) => void | Promise<void>, after = 0): Promise<void> {
        let cursor = after, attempts = 0;
        while (!signal.aborted) {
            let response: Response;
            try {
                response = await this.fetcher.call(globalThis, `/api/runs/${encodeURIComponent(runId)}/events`, {
                    signal, headers: this.headers({ Accept: 'text/event-stream', 'Last-Event-ID': String(cursor) }),
                });
            }
            catch (error) {
                if (signal.aborted)
                    return;
                if (++attempts > 5)
                    throw new ApiError(503, 'events_unavailable', 'Run events are unavailable. Refresh to reconnect.');
                await this.wait(Math.min(500 * 2 ** attempts, 5000), signal);
                continue;
            }
            if (!response.ok)
                return this.failure(response);
            if (!response.body || !response.headers.get('Content-Type')?.includes('text/event-stream'))
                throw new ApiError(502, 'invalid_event', 'Invalid event stream.');
            try {
                for await (const message of parseSSE(response.body)) {
                    if (message.event === 'error') {
                        const error = JSON.parse(message.data).error;
                        throw new ApiError(500, error?.code ?? 'events_error', error?.message ?? 'Run event stream failed.');
                    }
                    const event = JSON.parse(message.data) as RunEvent;
                    const id = Number(message.id);
                    if (!Number.isSafeInteger(id) || id < 1 || event.event_id !== id || event.run_id !== runId)
                        throw new ApiError(502, 'invalid_event', 'Invalid run event identity.');
                    if (id <= cursor)
                        continue;
                    await onEvent(event);
                    cursor = id;
                    attempts = 0;
                    if (['run.completed', 'run.failed', 'run.cancelled', 'run.interrupted'].includes(event.type))
                        return;
                }
            }
            catch (error) {
                if (signal.aborted)
                    return;
                if (error instanceof ApiError || error instanceof SyntaxError)
                    throw error;
            }
            if (++attempts > 5)
                throw new ApiError(503, 'events_unavailable', 'Run events are unavailable. Refresh to reconnect.');
            await this.wait(Math.min(500 * 2 ** attempts, 5000), signal);
        }
    }
}
