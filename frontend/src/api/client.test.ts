import { describe, expect, it, vi } from 'vitest';
import { ApiClient, ApiError, parseSSE } from './client';
function stream(parts: string[]) {
    return new ReadableStream<Uint8Array>({ start(controller) {
            for (const part of parts)
                controller.enqueue(new TextEncoder().encode(part));
            controller.close();
        } });
}
describe('management transport', () => {
    it('preserves the browser fetch receiver for JSON and event requests', async () => {
        const fetcher = async function (this: unknown, input: RequestInfo | URL): Promise<Response> {
            if (this !== globalThis) throw new TypeError('Illegal invocation');
            if (String(input).endsWith('/events')) return new Response(stream(['id: 1\nevent: run.completed\ndata: {"run_id":"r","event_id":1,"type":"run.completed"}\n\n']), { headers: { 'Content-Type': 'text/event-stream' } });
            return new Response('{"graphs":[]}');
        };
        const client = new ApiClient(() => '', fetcher, async () => {});
        await expect(client.json('/api/graphs')).resolves.toEqual({ graphs: [] });
        await expect(client.events('r', new AbortController().signal, () => {})).resolves.toBeUndefined();
    });
    it('keeps authorization in headers and propagates revision conflicts without retry', async () => {
        const fetcher = vi.fn<typeof fetch>(async () => new Response(JSON.stringify({ error: { code: 'revision_conflict', message: 'Reload the graph.', type: 'invalid_request_error' } }), { status: 409 }));
        const client = new ApiClient(() => 'private', fetcher);
        await expect(client.json('/api/graphs/g', { method: 'PUT', body: '{}' })).rejects.toMatchObject({ status: 409, code: 'revision_conflict' });
        expect(fetcher).toHaveBeenCalledTimes(1);
        expect(fetcher.mock.calls[0][0]).toBe('/api/graphs/g');
        expect(new Headers(fetcher.mock.calls[0][1]?.headers).get('Authorization')).toBe('Bearer private');
    });
    it('handles split UTF-8, CRLF, comments and multiline data', async () => {
        const encoded = new TextEncoder().encode(': heartbeat\r\nid: 7\r\nevent: tools.accepted\r\ndata: {"text":\r\ndata: "é"}\r\n\r\n');
        const chunks = new ReadableStream<Uint8Array>({ start(c) { for (const byte of encoded)
                c.enqueue(new Uint8Array([byte])); c.close(); } });
        const events = [];
        for await (const event of parseSSE(chunks))
            events.push(event);
        expect(events).toEqual([{ id: '7', event: 'tools.accepted', data: '{"text":\n"é"}' }]);
    });
    it('reconnects read-only event fetch with last committed cursor and stops on terminal event', async () => {
        const event = (id: number, type: string) => `id: ${id}\nevent: ${type}\ndata: ${JSON.stringify({ run_id: 'r', event_id: id, type, created_at: '2026-10-04T00:00:00Z', payload: {} })}\n\n`;
        const fetcher = vi.fn<typeof fetch>().mockResolvedValueOnce(new Response(stream([event(1, 'run.running')]), { headers: { 'Content-Type': 'text/event-stream' } })).mockResolvedValueOnce(new Response(stream([event(2, 'run.completed')]), { headers: { 'Content-Type': 'text/event-stream' } }));
        const ids: number[] = [];
        await new ApiClient(() => 'secret', fetcher, async () => { }).events('r', new AbortController().signal, event => { ids.push(event.event_id); });
        expect(ids).toEqual([1, 2]);
        expect(new Headers(fetcher.mock.calls[1][1]?.headers).get('Last-Event-ID')).toBe('1');
        expect(new Headers(fetcher.mock.calls[1][1]?.headers).get('Authorization')).toBe('Bearer secret');
    });
    it('does not endlessly reconnect authentication failures or error events', async () => {
        const denied = vi.fn<typeof fetch>().mockResolvedValue(new Response('{}', { status: 401 }));
        await expect(new ApiClient(() => '', denied).events('r', new AbortController().signal, () => { })).rejects.toBeInstanceOf(ApiError);
        expect(denied).toHaveBeenCalledTimes(1);
        const failure = vi.fn<typeof fetch>().mockResolvedValue(new Response(stream(['event: error\ndata: {"error":{"code":"storage_error","message":"Unavailable","type":"server_error"}}\n\n']), { headers: { 'Content-Type': 'text/event-stream' } }));
        await expect(new ApiClient(() => '', failure).events('r', new AbortController().signal, () => { })).rejects.toMatchObject({ code: 'storage_error' });
    });
    it('does not acknowledge an incomplete frame, and closes the reader on early termination', async () => {
        const messages = [];
        for await (const message of parseSSE(stream(['id: 8\ndata: unfinished'])))
            messages.push(message);
        expect(messages).toEqual([]);
        const cancel = vi.fn();
        const body = new ReadableStream<Uint8Array>({ start(c) { c.enqueue(new TextEncoder().encode('id: 1\ndata: ready\n\n')); }, cancel });
        for await (const message of parseSSE(body)) {
            expect(message.data).toBe('ready');
            break;
        }
        expect(cancel).toHaveBeenCalledTimes(1);
    });
    it('rejects mismatched run identity instead of advancing the event cursor', async () => {
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(stream(['id: 4\nevent: run.completed\ndata: {"run_id":"different","event_id":4,"type":"run.completed"}\n\n']), { headers: { 'Content-Type': 'text/event-stream' } }));
        const received = vi.fn();
        await expect(new ApiClient(() => '', fetcher).events('r', new AbortController().signal, received)).rejects.toMatchObject({ code: 'invalid_event' });
        expect(received).not.toHaveBeenCalled();
    });
    it('replays neither duplicate committed events nor mutation requests after transport failure', async () => {
        const frame = (id: number, type: string) => `id: ${id}\nevent: ${type}\ndata: ${JSON.stringify({ run_id: 'r', event_id: id, type, created_at: '2026-10-04T00:00:00Z', payload: {} })}\n\n`;
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(stream([frame(3, 'run.running') + frame(4, 'run.completed')]), { headers: { 'Content-Type': 'text/event-stream' } }));
        const received = vi.fn();
        await new ApiClient(() => '', fetcher).events('r', new AbortController().signal, received, 3);
        expect(received).toHaveBeenCalledTimes(1);
        expect(received.mock.calls[0][0].event_id).toBe(4);
        const unavailable = vi.fn<typeof fetch>().mockRejectedValue(new TypeError('Network failure'));
        await expect(new ApiClient(() => '', unavailable).json('/api/runs', { method: 'POST', body: '{}' })).rejects.toThrow('Network failure');
        expect(unavailable).toHaveBeenCalledTimes(1);
    });
});
