"""RD1-only durable continuation experiment; this is not the product engine.

The proxy never executes tools. It exposes native function calls to real Hermes,
and sends each returned result only to the activation that requested it.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

HERMES_SHA = "caed552de1c8a8f9983bc555512412a1ac0e0a9e"
DEFAULT_HERMES = Path("C:/Users/pkupr/AppData/Local/hermes/hermes-agent")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class BridgeError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def latest_segment(messages):
    """Only the latest assistant tool segment may route a continuation."""
    suffix = []
    for message in reversed(messages):
        role = message.get("role")
        if role == "assistant":
            if message.get("tool_calls"):
                return [m for m in reversed(suffix) if m.get("role") == "tool"], any(
                    m.get("role") == "user" for m in suffix
                )
            return [], False
        suffix.append(message)
    tools = [m for m in reversed(suffix) if m.get("role") == "tool"]
    return tools, bool(tools and any(m.get("role") == "user" for m in suffix))


def completion(message, finish="stop"):
    return {
        "id": "chatcmpl_" + uuid.uuid4().hex,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "cg/research",
        "choices": [{"index": 0, "message": message, "finish_reason": finish}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }


class ResearchBridge:
    def __init__(self, database, fixture, owners=1, upstream=None, model=None):
        self.db = sqlite3.connect(database, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.fixture = Path(fixture)
        self.owners = owners
        self.upstream = upstream
        self.model = model
        self.model_calls = 0
        self.trace = []
        self.db.executescript(
            "CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,state TEXT NOT NULL);"
            "CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,"
            "owner TEXT NOT NULL,internal_id TEXT NOT NULL,arguments_hash TEXT NOT NULL,"
            "delivered INTEGER NOT NULL DEFAULT 0,result TEXT);"
            "CREATE TABLE IF NOT EXISTS replay(hash TEXT PRIMARY KEY,response TEXT NOT NULL);"
        )
        self.db.commit()
        for row in self.db.execute("SELECT id,state FROM runs").fetchall():
            state = json.loads(row["state"])
            if state["status"] == "running":
                state["status"] = "interrupted"
                self.save(state)

    def close(self):
        self.db.close()

    def mappings(self):
        return [
            dict(row)
            for row in self.db.execute("SELECT * FROM calls ORDER BY owner,id")
        ]

    def state(self, run_id=None):
        if run_id:
            row = self.db.execute(
                "SELECT state FROM runs WHERE id=?", (run_id,)
            ).fetchone()
        else:
            row = self.db.execute(
                "SELECT state FROM runs ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
        return json.loads(row[0])

    def save(self, state):
        self.db.execute(
            "UPDATE runs SET state=? WHERE id=?", (canonical(state), state["id"])
        )
        self.db.commit()

    def owner_fixture(self, owner):
        return self.fixture.with_name(
            self.fixture.stem + "-" + owner + self.fixture.suffix
        )

    def model_request(self, messages, tools=None, require_read=False):
        self.model_calls += 1
        started = time.perf_counter()
        request = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": 0,
            "max_tokens": 512,
            "reasoning_effort": "none",
        }
        if tools:
            request["tools"] = tools
        if require_read:
            request["tool_choice"] = {
                "type": "function",
                "function": {"name": "read_file"},
            }
        self.trace.append({"upstream_request": request})
        wire = urllib.request.Request(
            self.upstream.rstrip("/") + "/chat/completions",
            data=canonical(request).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(wire, timeout=300) as response:
            result = json.load(response)
        self.trace.append(
            {
                "upstream_response": result,
                "elapsed_seconds": round(time.perf_counter() - started, 4),
            }
        )
        if result["choices"][0]["finish_reason"] == "length":
            raise BridgeError("model_length_before_completion")
        return result["choices"][0]["message"]

    def start(self, request, namespace):
        state = {
            "id": uuid.uuid4().hex,
            "status": "running",
            "namespace": namespace,
            "model": request["model"],
            "context": request["messages"],
            "nodes": {},
            "parallel": request.get("parallel_tool_calls", True),
            "tools": request.get("tools", []),
        }
        self.db.execute(
            "INSERT INTO runs VALUES (?,?)", (state["id"], canonical(state))
        )
        self.db.commit()
        for owner in "ab"[: self.owners]:
            path = str(self.owner_fixture(owner))
            prompt = {
                "role": "system",
                "content": f"Research node {owner}. Use read_file to read exactly {path}. After its result, return the fixture text in one short sentence. Do not call any other tools.",
            }
            node = {
                "messages": state["context"] + [prompt],
                "results": [],
                "payload": None,
            }
            if self.upstream:
                message = self.model_request(
                    node["messages"], state["tools"], require_read=True
                )
            else:
                self.model_calls += 1
                message = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "collision",
                            "type": "function",
                            "function": {
                                "name": "read_file",
                                "arguments": canonical({"path": path}),
                            },
                        }
                    ],
                }
            calls = message.get("tool_calls") or []
            if len(calls) != 1:
                raise BridgeError("model_must_emit_one_native_read")
            call = calls[0]
            arguments = json.loads(call["function"]["arguments"])
            if (
                call["function"]["name"] != "read_file"
                or Path(arguments.get("path", "")).resolve() != Path(path).resolve()
            ):
                raise BridgeError("unsafe_model_tool_request")
            external_id = "cg_" + uuid.uuid4().hex
            node["messages"].append(message)
            node["external"] = {**call, "id": external_id}
            state["nodes"][owner] = node
            self.db.execute(
                "INSERT INTO calls(id,run_id,owner,internal_id,arguments_hash) VALUES (?,?,?,?,?)",
                (external_id, state["id"], owner, call["id"], digest(arguments)),
            )
        state["status"] = "waiting_tools"
        self.save(state)
        return self.deliver(state)

    def deliver(self, state):
        pending = list(
            self.db.execute(
                "SELECT * FROM calls WHERE run_id=? AND delivered=0 ORDER BY owner",
                (state["id"],),
            )
        )
        if not state["parallel"]:
            pending = pending[:1]
        if pending:
            calls = [state["nodes"][row["owner"]]["external"] for row in pending]
            for row in pending:
                self.db.execute("UPDATE calls SET delivered=1 WHERE id=?", (row["id"],))
            self.db.commit()
            return completion(
                {"role": "assistant", "content": None, "tool_calls": calls},
                "tool_calls",
            )
        if any(n["payload"] is None for n in state["nodes"].values()):
            response = completion({"role": "assistant", "content": None})
            response["research_status"] = "waiting_tools"
            return response
        payloads = [
            {"node_id": owner, "port": owner, "payload": node["payload"]}
            for owner, node in sorted(state["nodes"].items())
        ]
        if self.upstream:
            state["status"] = "running"
            self.save(state)
            final = self.model_request(
                state["context"]
                + [
                    {
                        "role": "system",
                        "content": "Synthesize the research node inputs. Quote each fixture token exactly. Answer briefly.",
                    },
                    {"role": "user", "content": canonical(payloads)},
                ]
            )
            if final.get("tool_calls"):
                raise BridgeError("synthesis_tools_forbidden")
            content = final["content"]
        else:
            self.model_calls += 1
            content = " | ".join(f"{p['node_id']}:{p['payload']}" for p in payloads)
        state["status"] = "completed"
        state["final_payloads"] = payloads
        self.save(state)
        return completion({"role": "assistant", "content": content})

    def handle(self, request, namespace="anonymous"):
        results, mixed = latest_segment(request["messages"])
        if not results:
            return self.start(request, namespace)
        rows = []
        for result in results:
            row = self.db.execute(
                "SELECT * FROM calls WHERE id=?", (result["tool_call_id"],)
            ).fetchone()
            if row is None:
                raise BridgeError("unknown_tool_id")
            if not row["delivered"]:
                raise BridgeError("undelivered_tool_id")
            rows.append(row)
        if len({row["run_id"] for row in rows}) != 1:
            raise BridgeError("ambiguous_runs")
        state = self.state(rows[0]["run_id"])
        if request["model"] != state["model"] or namespace != state["namespace"]:
            raise BridgeError("namespace_model_mismatch")
        if mixed:
            raise BridgeError("mixed_new_turn")
        for row, result in zip(rows, results):
            if row["result"] is not None and row["result"] != canonical(
                result["content"]
            ):
                raise BridgeError("changed_result")
        key = digest({"namespace": namespace, "run": state["id"], "request": request})
        cached = self.db.execute(
            "SELECT response FROM replay WHERE hash=?", (key,)
        ).fetchone()
        if cached:
            return json.loads(cached[0])
        if state["status"] == "completed":
            raise BridgeError("closed_continuation")
        if state["status"] == "interrupted":
            raise BridgeError("interrupted")
        for row, result in zip(rows, results):
            if row["result"] is not None:
                continue
            node = state["nodes"][row["owner"]]
            node["results"].append(result["content"])
            node["messages"].append(
                {
                    "role": "tool",
                    "tool_call_id": row["internal_id"],
                    "content": result["content"],
                }
            )
            self.db.execute(
                "UPDATE calls SET result=? WHERE id=?",
                (canonical(result["content"]), row["id"]),
            )
            self.save(state)
            if self.upstream:
                state["status"] = "running"
                self.save(state)
                final = self.model_request(node["messages"])
                if final.get("tool_calls"):
                    raise BridgeError("research_single_round_only")
                node["payload"] = final["content"]
                state["status"] = "waiting_tools"
            else:
                self.model_calls += 1
                node["payload"] = result["content"]
        self.save(state)
        response = self.deliver(state)
        self.db.execute("INSERT INTO replay VALUES (?,?)", (key, canonical(response)))
        self.db.commit()
        return response


def sse_chunks(response):
    base = {k: response[k] for k in ("id", "created", "model")}
    base["object"] = "chat.completion.chunk"
    message = response["choices"][0]["message"]
    deltas = [{"role": "assistant"}]
    if message.get("tool_calls"):
        for index, call in enumerate(message["tool_calls"]):
            args = call["function"]["arguments"]
            deltas.append(
                {
                    "tool_calls": [
                        {
                            "index": index,
                            "id": call["id"],
                            "type": "function",
                            "function": {
                                "name": call["function"]["name"],
                                "arguments": args[:5],
                            },
                        }
                    ]
                }
            )
            deltas.append(
                {"tool_calls": [{"index": index, "function": {"arguments": args[5:]}}]}
            )
    else:
        deltas.append({"content": message["content"]})
    for delta in deltas:
        yield canonical(
            {**base, "choices": [{"index": 0, "delta": delta, "finish_reason": None}]}
        )
    yield canonical(
        {
            **base,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": response["choices"][0]["finish_reason"],
                }
            ],
        }
    )
    yield "[DONE]"


def source_evidence(hermes):
    sha = subprocess.check_output(
        ["git", "-C", str(hermes), "rev-parse", "HEAD"], text=True
    ).strip()
    if sha != HERMES_SHA:
        raise RuntimeError(f"Unreviewed Hermes revision {sha}")
    names = [
        "run_agent.py",
        "model_tools.py",
        "toolsets.py",
        "hermes_cli/env_loader.py",
        "hermes_cli/timeouts.py",
        "agent/agent_init.py",
        "agent/conversation_loop.py",
        "agent/chat_completion_helpers.py",
        "agent/agent_runtime_helpers.py",
        "agent/context_compressor.py",
        "agent/auxiliary_client.py",
        "agent/model_metadata.py",
        "agent/conversation_compression.py",
        "agent/tool_executor.py",
        "agent/transports/chat_completions.py",
        "tools/file_tools.py",
        "tools/file_operations.py",
        "hermes_cli/runtime_provider.py",
    ]
    sources = {}
    for name in names:
        raw = (hermes / name).read_bytes()
        pinned = subprocess.check_output(
            ["git", "-C", str(hermes), "show", f"{sha}:{name}"]
        )
        normalized = raw.replace(b"\r\n", b"\n")
        matches = normalized == pinned.replace(b"\r\n", b"\n")
        sources[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "normalized_sha256": hashlib.sha256(normalized).hexdigest(),
            "matches_revision_normalized": matches,
        }
        if not matches:
            raise RuntimeError(f"Exercised source differs from pin: {name}")
    dirty = subprocess.check_output(
        ["git", "-C", str(hermes), "status", "--porcelain"], text=True
    ).splitlines()
    return {"git_sha": sha, "dirty_entries": len(dirty), "sources": sources}


def load_hermes(hermes, work):
    """Only startup dotenv discovery is replaced; production protocol is intact."""
    os.environ["HERMES_HOME"] = str(work / "home")
    os.environ["TERMINAL_ENV"] = "local"
    os.environ["TERMINAL_CWD"] = str(work)
    os.environ["HERMES_API_TIMEOUT"] = "300"
    for key in list(os.environ):
        if key.endswith(("_API_KEY", "_TOKEN", "_SECRET", "_KEY")):
            os.environ.pop(key)
    (work / "home").mkdir(exist_ok=True)
    sys.path.insert(0, str(hermes))
    sys.path.append(str(hermes / "venv" / "Lib" / "site-packages"))
    with patch("hermes_cli.env_loader.load_hermes_dotenv", return_value=[]):
        from run_agent import AIAgent
    return AIAgent


def run_hermes(
    work,
    owners=1,
    stream=False,
    upstream=None,
    model=None,
    hermes=DEFAULT_HERMES,
    restart=False,
    compress=False,
    serial_tools=False,
):
    started = time.perf_counter()
    work = Path(work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    if compress:
        if not upstream:
            raise ValueError("Compression research requires the live upstream")
        (work / "home").mkdir(exist_ok=True)
        (work / "home" / "config.yaml").write_text(
            canonical(
                {
                    "auxiliary": {
                        "compression": {
                            "model": model,
                            "provider": "custom",
                            "base_url": upstream,
                            "api_key": "dummy-key",
                            "timeout": 300,
                            "extra_body": {"reasoning_effort": "none"},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
    pin = source_evidence(hermes)
    fixture = work / "fixture.txt"
    for owner in "ab"[:owners]:
        fixture.with_name(f"fixture-{owner}.txt").write_text(
            f"fixture-token-{owner}\n", encoding="utf-8"
        )
    bridge = ResearchBridge(
        work / "checkpoint.sqlite", fixture, owners, upstream, model
    )
    trace = []
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            body = canonical(
                {
                    "object": "list",
                    "data": [
                        {
                            "id": "cg/research",
                            "object": "model",
                            "owned_by": "cognitive-graph",
                        }
                    ],
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            nonlocal bridge, restart
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path != "/v1/chat/completions":
                self.send_response(404)
                self.end_headers()
                return
            trace.append({"client_request": request})
            try:
                response = bridge.handle(request)
                trace.append({"proxy_response": response})
                if restart and response["choices"][0]["finish_reason"] == "tool_calls":
                    old_trace = bridge.trace
                    bridge.close()
                    bridge = ResearchBridge(
                        work / "checkpoint.sqlite", fixture, owners, upstream, model
                    )
                    bridge.trace = old_trace
                    trace.append({"checkpoint_reopened_before_tool_results": True})
                    restart = False
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/event-stream"
                    if request.get("stream")
                    else "application/json",
                )
                self.send_header("Connection", "close")
                self.end_headers()
                if request.get("stream"):
                    self.wfile.write(b": research-heartbeat\n\n")
                    for chunk in sse_chunks(response):
                        self.wfile.write(f"data: {chunk}\n\n".encode())
                        self.wfile.flush()
                else:
                    self.wfile.write(canonical(response).encode())
            except Exception as exc:
                trace.append({"proxy_error": type(exc).__name__, "code": str(exc)})
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    canonical(
                        {"error": {"message": str(exc), "type": "upstream_error"}}
                    ).encode()
                )

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    old_cwd = Path.cwd()
    try:
        os.chdir(work)
        agent_class = load_hermes(hermes, work)
        agent = agent_class(
            base_url=f"http://127.0.0.1:{server.server_port}/v1",
            api_key="dummy-key",
            provider="custom",
            api_mode="chat_completions",
            model="cg/research",
            max_iterations=8,
            tool_delay=0,
            enabled_toolsets=["file"],
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            save_trajectories=False,
            checkpoints_enabled=False,
            request_overrides={"parallel_tool_calls": False} if serial_tools else None,
            tool_complete_callback=lambda *args, **kwargs: calls.append(
                {"args": str(args)[:100], "kwargs": list(kwargs)}
            ),
        )
        agent.tools = [
            tool for tool in agent.tools if tool["function"]["name"] == "read_file"
        ]
        agent.valid_tool_names = {"read_file"}
        agent._skip_mcp_refresh = True
        agent._disable_streaming = not stream
        if compress:
            from agent.context_compressor import ContextCompressor

            compressor = ContextCompressor(
                model=model,
                provider="custom",
                api_mode="chat_completions",
                base_url=upstream,
                api_key="dummy-key",
                config_context_length=262144,
                protect_first_n=1,
                protect_last_n=4,
                quiet_mode=True,
            )
            compressor.tail_token_budget = 512
            sanitize = agent._sanitize_api_messages
            compressed_once = False

            def force_real_compression(messages):
                nonlocal compressed_once
                if not compressed_once and any(
                    m.get("role") == "tool" for m in messages
                ):
                    old_turns = []
                    for index in range(12):
                        old_turns.extend(
                            [
                                {
                                    "role": "user",
                                    "content": f"Historical closed test turn {index}: "
                                    + "Inert research notes. " * 60,
                                },
                                {
                                    "role": "assistant",
                                    "content": f"Historical closed test answer {index}. No pending task. "
                                    + "All old work is complete. " * 60,
                                },
                            ]
                        )
                    expanded = [messages[0], *old_turns, *messages[1:]]
                    compressed_messages = compressor.compress(
                        copy.deepcopy(expanded), force=True
                    )
                    before, after = (
                        latest_segment(expanded)[0],
                        latest_segment(compressed_messages)[0],
                    )
                    if (
                        compressor.compression_count != 1
                        or len(compressed_messages) >= len(expanded)
                        or before != after
                    ):
                        raise RuntimeError(
                            "Real compression did not preserve latest tool IDs/results"
                        )
                    trace.append(
                        {
                            "real_compression": {
                                "before_messages": len(expanded),
                                "after_messages": len(compressed_messages),
                                "compression_count": compressor.compression_count,
                                "latest_ids_before": [
                                    m["tool_call_id"] for m in before
                                ],
                                "latest_ids_after": [m["tool_call_id"] for m in after],
                                "latest_results_unchanged": before == after,
                                "compressed_messages": compressed_messages,
                                "summary_model": model,
                                "summary_endpoint": upstream,
                                "forced_research_tail_budget": 512,
                            }
                        }
                    )
                    compressed_once = True
                    messages = compressed_messages
                return sanitize(messages)

            agent._sanitize_api_messages = force_real_compression
        result = agent.run_conversation(
            "Read the research fixture and synthesize the node results.",
            system_message="Read only the dedicated research fixture. Never modify files.",
            task_id="cg-rd1-research",
        )
        messages = result.get("messages", [])
        count = sum(m.get("role") == "tool" for m in messages)
        pending = bridge.mappings()
        for mapping in pending:
            if mapping["result"] is None or "fixture-token" not in mapping["result"]:
                raise RuntimeError(
                    "Actual Hermes fixture read did not produce expected token"
                )
        for request_trace in trace:
            request = request_trace.get("client_request")
            if request and latest_segment(request["messages"])[0]:
                cached = bridge.handle(request)
                request_trace["exact_replay_matches"] = cached == next(
                    t["proxy_response"]
                    for t in trace[trace.index(request_trace) + 1 :]
                    if "proxy_response" in t
                )
        state = bridge.state()
        if (
            not result.get("completed")
            or state["status"] != "completed"
            or count != owners
        ):
            raise RuntimeError("Real Hermes graph continuation did not complete")
        output = {
            "completed": result.get("completed"),
            "final_response": result.get("final_response"),
            "api_calls": result.get("api_calls"),
            "tool_results": count,
            "stream": stream,
            "owners": owners,
            "upstream": upstream,
            "physical_model": model,
            "hermes_pin": pin,
            "runtime_versions": {
                n: importlib.metadata.version(n)
                for n in ("hermes-agent", "openai", "httpx")
            },
            "client_trace": trace,
            "upstream_trace": bridge.trace,
            "mappings": pending,
            "state": state,
            "wall_seconds": round(time.perf_counter() - started, 4),
            "client_request_keys": sorted(
                {
                    key
                    for item in trace
                    if "client_request" in item
                    for key in item["client_request"]
                }
            ),
        }
        return output
    finally:
        os.chdir(old_cwd)
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        bridge.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-root", type=Path, default=DEFAULT_HERMES)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--upstream")
    parser.add_argument("--model")
    parser.add_argument("--owners", type=int, choices=(1, 2), default=1)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--serial-tools", action="store_true")
    parser.add_argument(
        "--trace", type=Path, default=Path("experiments/hermes-traces.json")
    )
    args = parser.parse_args()
    if bool(args.upstream) != bool(args.model):
        parser.error("--upstream and --model must be supplied together")
    result = run_hermes(
        args.work_dir,
        args.owners,
        args.stream,
        args.upstream,
        args.model,
        args.hermes_root,
        args.restart,
        args.compress,
        args.serial_tools,
    )
    args.trace.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        canonical(
            {
                k: result[k]
                for k in (
                    "completed",
                    "api_calls",
                    "tool_results",
                    "final_response",
                    "physical_model",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
