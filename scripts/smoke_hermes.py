"""Pinned real Hermes/Ollama smoke through the production Cognitive Graph API."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class SmokeFailure(RuntimeError):
    """A locally authored assertion whose message contains no SDK data or secrets."""


class NativeBackend:
    """Own one production Uvicorn process and fresh data for a native-only fallback."""

    def __init__(self, python: Path, work: Path, base: str, ollama: str, token: str):
        self.python, self.base = python.resolve(), base
        if not self.python.is_file():
            raise SmokeFailure("Existing pinned backend interpreter is unavailable")
        self.data = work / "backend-data"
        self.data.mkdir(exist_ok=False)
        self.log = (work / "native-backend.log").open("x", encoding="utf-8")
        names = [
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "HOME",
            "USERPROFILE",
            "LOCALAPPDATA",
            "APPDATA",
            "NO_PROXY",
            "CG_MAX_PARALLEL_LLM",
            "CG_MAX_ACTIVE_RUNS",
            "CG_MAX_QUEUED_RUNS",
            "CG_LLM_TIMEOUT_SECONDS",
            "CG_RUN_ACTIVE_TIMEOUT_SECONDS",
            "CG_TOOL_WAIT_TIMEOUT_SECONDS",
            "CG_MAX_NODE_EXECUTIONS",
            "CG_MAX_TOOL_ROUNDS",
            "CG_HISTORY_RETENTION_DAYS",
        ]
        self.env = {name: os.environ[name] for name in names if name in os.environ}
        self.env.update(CG_DATA_DIR=str(self.data), OLLAMA_BASE_URL=ollama, CG_API_TOKEN=token)
        self.token, self.process = token, None
        self.source_paths = [
            "main.py",
            "runtime/engine.py",
            "storage/repository.py",
            "providers/ollama.py",
            "providers/sse.py",
            "tools/bridge.py",
            "api/chat.py",
            "api/graphs.py",
            "api/runs.py",
            "contracts/api.py",
            "contracts/interfaces.py",
        ]
        self.sources = self.hash_sources()

    def hash_sources(self):
        return {
            name: hashlib.sha256((ROOT / "backend/app" / name).read_bytes()).hexdigest()
            for name in self.source_paths
        }

    def start(self, *, initial: bool = False):
        if self.hash_sources() != self.sources:
            raise SmokeFailure(
                "Native production source changed during the fixture; snapshot evidence invalid"
            )
        if initial:
            with socket.socket() as port:
                port.bind(("127.0.0.1", 8000))
        self.process = subprocess.Popen(
            [
                str(self.python),
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                str(ROOT / "backend"),
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--workers",
                "1",
                "--timeout-graceful-shutdown",
                "30",
                "--no-access-log",
            ],
            cwd=ROOT,
            env=self.env,
            stdin=subprocess.DEVNULL,
            stdout=self.log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        deadline = time.monotonic() + 90
        while True:
            if self.process.poll() is not None:
                raise SmokeFailure(
                    "Owned native backend exited before readiness; retained log identifies failure"
                )
            try:
                health, _ = exchange(self.base, "/health/ready", self.token, timeout=3)
                if health["storage_ready"]:
                    break
            except (OSError, KeyError):
                pass
            if time.monotonic() >= deadline:
                raise SmokeFailure("Owned native backend did not become ready within90seconds")
            time.sleep(0.25)

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=35)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)

    def restart(self, run_id):
        before_pid = self.process.pid
        self.stop()
        before_exit = self.process.returncode
        self.start()
        if before_pid == self.process.pid:
            raise SmokeFailure("Native waiting-tool restart did not replace the owned process")
        return {
            "kind": "owned native production process",
            "run_id": run_id,
            "pid_before": before_pid,
            "pid_after": self.process.pid,
            "prior_exit_code": before_exit,
            "data_directory": str(self.data),
            "stop_semantics": (
                "terminate owned process; Windows is abrupt, Linux SIGTERM is graceful"
            ),
        }

    def close(self):
        self.stop()
        self.log.close()


def observe_original_clients(agent, request_hook, response_hook):
    """Attach httpx observation hooks to the original native factory's SDK objects."""
    original = agent._create_openai_client
    lifecycle = []

    def attach(client):
        hooks = client._client.event_hooks
        for name, callback in (("request", request_hook), ("response", response_hook)):
            callbacks = hooks.setdefault(name, [])
            if callback not in callbacks:
                callbacks.append(callback)

    def observed_factory(client_kwargs, *, reason, shared):
        client = original(client_kwargs, reason=reason, shared=shared)
        attach(client)
        lifecycle.append({"reason": reason, "shared": shared})
        return client

    attach(agent.client)
    agent._create_openai_client = observed_factory

    def restore():
        agent._create_openai_client = original

    return restore, lifecycle


def exchange(
    base: str, path: str, token: str, body: dict | None = None, *, timeout: float = 310
) -> tuple[object, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    message = urllib.request.Request(
        base + path,
        data=None if body is None else json.dumps(body).encode(),
        headers=headers,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(message, timeout=timeout) as response:
        response_headers = dict(response.headers)
        if "text/event-stream" not in response.headers.get("Content-Type", ""):
            return json.load(response), response_headers
        chunks = []
        done = False
        for raw in response:
            line = raw.decode().strip()
            if line == "event: error":
                raise SmokeFailure("Production SSE returned an error")
            if line == "data: [DONE]":
                done = True
                break
            if line.startswith("data: "):
                chunk = json.loads(line[6:])
                if "error" in chunk:
                    raise SmokeFailure("Production SSE returned an error envelope")
                chunks.append(chunk)
        if not done:
            raise SmokeFailure("Successful production SSE did not terminate with DONE")
        return chunks, response_headers


def graph_fixture(graph_id: str, model: str, paths: list[Path], effort: str | None) -> dict:
    nodes = [{"id": "input", "type": "input", "input_id": "chat"}]
    edges = []
    generation = {"temperature": 0.0, "max_tokens": 1024}
    if effort:
        generation["reasoning_effort"] = effort
    for index, path in enumerate(paths):
        owner = f"owner{index}"
        nodes.append(
            {
                "id": owner,
                "type": "llm",
                "tools_enabled": True,
                "generation": generation,
                "system_prompt": (
                    f"Use read_file exactly once to read this dedicated fixture: {path}. "
                    "No other paths or tools are permitted. After receiving its result, "
                    "return the complete fixture token in one sentence without more calls."
                ),
            }
        )
        edges.extend(
            [
                {
                    "id": "input-" + owner,
                    "source": "input",
                    "target": owner,
                    "target_port": "question",
                    "kind": "forward",
                },
                {
                    "id": owner + "-final",
                    "source": owner,
                    "target": "final",
                    "target_port": owner,
                    "kind": "forward",
                },
            ]
        )
    nodes.extend(
        [
            {
                "id": "final",
                "type": "llm",
                "tools_enabled": False,
                "generation": generation,
                "system_prompt": (
                    "Return every supplied fixture token verbatim in one short sentence."
                ),
            },
            {"id": "output", "type": "output"},
        ]
    )
    edges.append(
        {
            "id": "final-output",
            "source": "final",
            "target": "output",
            "target_port": "answer",
            "kind": "forward",
        }
    )
    return {
        "schema_version": 1,
        "id": graph_id,
        "name": "Dedicated real Hermes smoke",
        "revision": 1,
        "base_model": model,
        "inputs": [{"id": "chat", "required": True}],
        "nodes": nodes,
        "edges": edges,
        "loops": [],
        "output_node_id": "output",
    }


def observation(detail: dict, tool_count: int) -> dict:
    run = detail["run"]
    return {
        "status": run["status"],
        "graph_hash": run["graph_hash"],
        "node_executions": run["node_executions"],
        "upstream_attempts": run["upstream_attempts"],
        "tool_rounds": run["tool_rounds"],
        "hermes_tool_executions": tool_count,
        "activations": detail["activations"],
        "pending_tools": detail["pending_tools"],
        "output": detail["output"],
        "error": detail["error"],
    }


def owned_restart(base: str, token: str, project: str, compose_file: Path, context: str | None):
    """Return a one-shot restart callable for the explicitly selected smoke project."""
    if not re.fullmatch(r"cg-[a-z0-9][a-z0-9_-]*", project):
        raise SmokeFailure("Waiting restart requires an explicitly named dedicated cg-* project")
    docker = ["docker", *(["--context", context] if context else [])]
    compose = [*docker, "compose", "-p", project, "-f", str(compose_file.resolve())]

    def command(arguments):
        result = subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            cwd=ROOT,
            timeout=90,
        )
        if result.returncode:
            raise SmokeFailure("Owned Compose restart command failed")
        return result.stdout.strip()

    def restart(run_id):
        container = command([*compose, "ps", "-q", "backend"])
        if not container or "\n" in container:
            raise SmokeFailure("Expected exactly one running owned backend")
        labels = json.loads(
            command([*docker, "inspect", container, "--format", "{{json .Config.Labels}}"])
        )
        mounts = json.loads(
            command([*docker, "inspect", container, "--format", "{{json .Mounts}}"])
        )
        if (
            labels.get("com.docker.compose.project") != project
            or labels.get("com.docker.compose.service") != "backend"
            or len(mounts) != 1
            or mounts[0].get("Name") != project + "_cg_data"
        ):
            raise SmokeFailure("Restart target is not the explicitly owned smoke service/volume")
        before = json.loads(command([*docker, "inspect", container, "--format", "{{json .State}}"]))
        command([*compose, "restart", "backend"])
        deadline = time.monotonic() + 120
        while True:
            try:
                health, _ = exchange(base, "/health/ready", token, timeout=3)
                if health["storage_ready"]:
                    break
            except (OSError, KeyError):
                pass
            if time.monotonic() >= deadline:
                raise SmokeFailure("Owned backend restart did not reach readiness")
            time.sleep(0.5)
        after = json.loads(command([*docker, "inspect", container, "--format", "{{json .State}}"]))
        if (
            not before["Running"]
            or not after["Running"]
            or before["StartedAt"] == after["StartedAt"]
            or before["Pid"] == after["Pid"]
        ):
            raise SmokeFailure("Actual backend process restart was not demonstrated")
        return {
            "project": project,
            "container": container,
            "run_id": run_id,
            "started_at_before": before["StartedAt"],
            "started_at_after": after["StartedAt"],
            "pid_before": before["Pid"],
            "pid_after": after["Pid"],
        }

    return restart


def run_case(
    base: str,
    model: str,
    hermes: Path,
    work: Path,
    token: str,
    stream: bool,
    effort: str | None,
    restart: Callable[[str], dict] | None = None,
    compression_url: str | None = None,
) -> dict:
    # These helpers verify the pinned files and isolate startup only. No research
    # HTTP server, Bridge, provider, compressor, or deterministic model is used.
    from experiments.hermes_bridge import load_hermes, source_evidence

    pin = source_evidence(hermes)
    plugin_path = hermes / "hermes_cli/plugins.py"
    raw = plugin_path.read_bytes()
    pinned = subprocess.check_output(
        ["git", "-C", str(hermes), "show", pin["git_sha"] + ":hermes_cli/plugins.py"]
    )
    if raw.replace(b"\r\n", b"\n") != pinned.replace(b"\r\n", b"\n"):
        raise SmokeFailure("Native fixture-blocking hook source differs from pinned Hermes")
    pin["sources"]["hermes_cli/plugins.py"] = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "matches_revision_normalized": True,
    }
    work.mkdir(parents=True, exist_ok=False)
    fixtures = [work / f"owner{index}.txt" for index in range(2)]
    tokens = ["fixture-token-" + uuid.uuid4().hex for _ in fixtures]
    for path, value in zip(fixtures, tokens, strict=True):
        path.write_text(value, encoding="utf-8")
    # The first case proves literal cg/synthesis selection. POST conflicts rather
    # than overwriting a user's existing graph; use a fresh smoke Compose project.
    graph_id = "hermes-" + uuid.uuid4().hex[:20] if stream else "synthesis"
    graph = graph_fixture(graph_id, model, fixtures, effort)
    exchange(base, "/api/graphs", token, graph)
    exchange(base, f"/api/graphs/{graph_id}/publish", token, {"expected_revision": 1})
    catalog, _ = exchange(base, "/v1/models", token)
    if "cg/" + graph_id not in {item["id"] for item in catalog["data"]}:
        raise SmokeFailure("Published native Hermes graph is absent from model discovery")
    old_cwd = Path.cwd()
    started = time.monotonic()
    calls = []
    blocked = []
    hook_seen = []
    requests = []
    responses = []
    run_ids = []
    agent = None
    context = None
    guard = None
    restart_evidence = None
    compression_evidence = None
    compressor = None
    restore_observer = None
    sdk_client_lifecycle = []
    try:
        if compression_url:
            (work / "home").mkdir(exist_ok=False)
            (work / "home/config.yaml").write_text(
                json.dumps(
                    {
                        "auxiliary": {
                            "compression": {
                                "model": model,
                                "provider": "custom",
                                "base_url": compression_url,
                                "api_key": "local-anonymous",
                                "timeout": 300,
                                "extra_body": {"reasoning_effort": "none"}
                                if effort == "none"
                                else {},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
        os.chdir(work)
        agent_class = load_hermes(hermes, work)
        if importlib.metadata.version("openai") != "2.24.0":
            raise SmokeFailure("Actual Hermes OpenAI dependency differs from G0 pin 2.24.0")
        from hermes_cli.plugins import PluginContext, PluginManifest, get_plugin_manager

        allowed = {path.resolve() for path in fixtures}

        def guard(tool_name, args, **_kwargs):
            path = args.get("path") if isinstance(args, dict) else None
            if (
                tool_name != "read_file"
                or not isinstance(path, str)
                or Path(path).resolve() not in allowed
            ):
                blocked.append({"tool": tool_name})
                return {
                    "action": "block",
                    "message": "Only dedicated smoke fixture reads are allowed",
                }
            hook_seen.append(str(Path(path).resolve()))
            return None

        context = PluginContext(
            PluginManifest(name="cg-smoke-fixture-boundary"), get_plugin_manager()
        )
        context.register_hook("pre_tool_call", guard)
        # Native resolver calls are checked before any model-driven execution.
        from hermes_cli.plugins import resolve_pre_tool_block

        if resolve_pre_tool_block("read_file", {"path": str(work / "forbidden.txt")}) is None:
            raise SmokeFailure("Native fixture guard did not reject an out-of-scope path")
        blocked.clear()
        agent = agent_class(
            base_url=base + "/v1",
            api_key=token or "local-anonymous",
            provider="custom",
            api_mode="chat_completions",
            model="cg/" + graph_id,
            max_iterations=24,
            max_tokens=1024,
            tool_delay=0,
            enabled_toolsets=["file"],
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            save_trajectories=False,
            checkpoints_enabled=False,
            request_overrides={"parallel_tool_calls": False},
            tool_complete_callback=lambda call_id, name, args, result: calls.append(
                {
                    "id": call_id,
                    "name": name,
                    "args": copy.deepcopy(args),
                    "result": result,
                }
            ),
        )
        agent.tools = [tool for tool in agent.tools if tool["function"]["name"] == "read_file"]
        agent.valid_tool_names = {"read_file"}
        agent._skip_mcp_refresh = True
        agent._disable_streaming = not stream

        def request_hook(message):
            if message.url.path.endswith("/chat/completions"):
                requests.append(json.loads(message.content))

        def response_hook(response):
            nonlocal restart_evidence
            if not response.request.url.path.endswith("/chat/completions"):
                return
            run_id = response.headers.get("X-CG-Run-ID")
            if run_id:
                run_ids.append(run_id)
            if "text/event-stream" not in response.headers.get("content-type", ""):
                wire = json.loads(response.read())
                responses.append(copy.deepcopy(wire))
                if (
                    restart
                    and restart_evidence is None
                    and wire["choices"][0]["finish_reason"] == "tool_calls"
                ):
                    if not run_id or calls:
                        raise SmokeFailure(
                            "Waiting restart must precede the first native tool effect"
                        )
                    before, _ = exchange(base, f"/api/runs/{run_id}", token)
                    if before["run"]["status"] != "waiting_tools":
                        raise SmokeFailure("Restart fixture is not at a safe durable tool boundary")
                    restart_evidence = restart(run_id)
                    after, _ = exchange(base, f"/api/runs/{run_id}", token)
                    if observation(before, 0) != observation(after, 0):
                        raise SmokeFailure(
                            "Actual backend restart changed IDs/owners/results/execution counters"
                        )
                    restart_evidence["pending_ids"] = [
                        item["tool_call_id"] for item in before["pending_tools"]
                    ]
                    restart_evidence["counts_unchanged_before_effects"] = True
                    restart_evidence["tool_effects_before_restart"] = 0

        # Native dispatch builds and closes an ORIGINAL SDK client per request.
        # The instance-local delegate adds public HTTP observation hooks only;
        # factory arguments, returned object, transport and ownership are unchanged.
        restore_observer, sdk_client_lifecycle = observe_original_clients(
            agent, request_hook, response_hook
        )
        if compression_url:
            from agent.context_compressor import ContextCompressor

            from experiments.hermes_bridge import latest_segment

            compressor = ContextCompressor(
                model=model,
                provider="custom",
                api_mode="chat_completions",
                base_url=compression_url,
                api_key="local-anonymous",
                config_context_length=262144,
                protect_first_n=1,
                protect_last_n=4,
                quiet_mode=True,
            )
            compressor.tail_token_budget = 512
            sanitize = agent._sanitize_api_messages

            def native_compression(messages):
                nonlocal compression_evidence
                if compression_evidence is None and any(m.get("role") == "tool" for m in messages):
                    old_turns = []
                    for index in range(12):
                        old_turns.extend(
                            [
                                {
                                    "role": "user",
                                    "content": f"Historical closed smoke turn{index}: "
                                    + "Inert fixture notes. " * 60,
                                },
                                {
                                    "role": "assistant",
                                    "content": f"Closed answer{index}; no pending task. "
                                    + "Old work complete. " * 60,
                                },
                            ]
                        )
                    expanded = [messages[0], *old_turns, *messages[1:]]
                    compressed = compressor.compress(copy.deepcopy(expanded), force=True)
                    before, after = (
                        latest_segment(expanded)[0],
                        latest_segment(compressed)[0],
                    )
                    if (
                        compressor.compression_count != 1
                        or len(compressed) >= len(expanded)
                        or before != after
                        or not before
                    ):
                        raise SmokeFailure(
                            "Real native compression did not preserve pending IDs/results"
                        )
                    compression_evidence = {
                        "before_messages": len(expanded),
                        "after_messages": len(compressed),
                        "compression_count": compressor.compression_count,
                        "pending_ids_before": [m["tool_call_id"] for m in before],
                        "pending_ids_after": [m["tool_call_id"] for m in after],
                        "results_unchanged": True,
                        "summary_model": model,
                        "summary_endpoint": compression_url,
                        "fixture_tail_token_budget": 512,
                    }
                    messages = compressed
                return sanitize(messages)

            # Exercise the original native compressor before original sanitation;
            # no client, compressor, executor or response implementation is replaced.
            agent._sanitize_api_messages = native_compression
        result = agent.run_conversation(
            "Read the dedicated smoke fixtures and synthesize every token.",
            system_message=(
                "Read only the explicitly specified smoke fixture files. Never modify files."
            ),
            task_id=graph_id,
        )
        if not result.get("completed") or len(calls) != 2 or blocked or len(hook_seen) != 2:
            raise SmokeFailure(
                "Actual Hermes did not complete exactly two allowed native fixture reads"
            )
        if not all(value in result.get("final_response", "") for value in tokens):
            raise SmokeFailure("Final synthesis omitted a fixture token")
        if not run_ids or len(set(run_ids)) != 1:
            raise SmokeFailure("Diagnostic responses do not identify one durable graph run")
        run_id = run_ids[0]
        detail, _ = exchange(base, f"/api/runs/{run_id}", token)
        if detail["run"]["status"] != "completed":
            raise SmokeFailure("Production run did not complete")
        owners = {item["tool_call_id"]: item["node_id"] for item in detail["pending_tools"]}
        for call in calls:
            path = Path(call["args"]["path"]).resolve()
            index = [p.resolve() for p in fixtures].index(path)
            if owners.get(call["id"]) != f"owner{index}" or tokens[index] not in str(
                call["result"]
            ):
                raise SmokeFailure("Native fixture result was not mapped to its owning activation")
        before = observation(detail, len(calls))
        continuation_count = 0
        for index, payload in enumerate(requests):
            # Latest relevant segment only; old historical tool messages are not a new replay.
            if not payload["messages"] or payload["messages"][-1]["role"] != "tool":
                continue
            replay, _ = exchange(base, "/v1/chat/completions", token, payload)
            if not stream:
                if replay != responses[index]:
                    raise SmokeFailure("Exact production continuation replay changed its response")
            else:
                repeat, _ = exchange(base, "/v1/chat/completions", token, payload)
                if repeat != replay:
                    raise SmokeFailure("Exact production SSE continuation replay changed chunks")
            current, _ = exchange(base, f"/api/runs/{run_id}", token)
            if observation(current, len(calls)) != before:
                raise SmokeFailure(
                    "Continuation replay changed durable execution, tools, or checkpoint"
                )
            continuation_count += 1
        if continuation_count != 2:
            raise SmokeFailure("Expected both serialized real Hermes continuations")
        if restart and restart_evidence is None:
            raise SmokeFailure("Required actual waiting-tool backend restart was not executed")
        if compression_url and compression_evidence is None:
            raise SmokeFailure("Required native pending-continuation compression was not executed")
        return {
            "stream": stream,
            "run_id": run_id,
            "graph_id": graph_id,
            "hermes_source": pin,
            "physical_model": model,
            "api_calls": len(requests),
            "original_sdk_client_lifecycle": sdk_client_lifecycle,
            "tool_executions": len(calls),
            "verified_continuations": continuation_count,
            "counts": {
                key: before[key]
                for key in (
                    "node_executions",
                    "upstream_attempts",
                    "tool_rounds",
                    "hermes_tool_executions",
                )
            },
            "owner_map": owners,
            "waiting_backend_restart": restart_evidence,
            "native_compression": compression_evidence,
            "native_guard_path": (
                "PluginContext.register_hook(pre_tool_call) -> resolve_pre_tool_block"
            ),
            "wall_seconds": round(time.monotonic() - started, 3),
            "versions": {
                name: importlib.metadata.version(name)
                for name in ("hermes-agent", "openai", "httpx")
            },
        }
    except Exception as exc:
        (work / "failure.json").write_text(
            json.dumps(
                {
                    "result": "FAILED; requested gates remain OPEN",
                    "error_type": type(exc).__name__,
                    "assertion": str(exc) if isinstance(exc, SmokeFailure) else None,
                    "graph_id": graph_id,
                    "hermes_source": pin,
                    "run_ids": sorted(set(run_ids)),
                    "api_calls_observed": len(requests),
                    "native_reads": len(calls),
                    "blocked_native_calls": len(blocked),
                    "guard_calls": len(hook_seen),
                    "original_sdk_client_lifecycle": sdk_client_lifecycle,
                    "restart": restart_evidence,
                    "compression": compression_evidence,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        raise
    finally:
        os.chdir(old_cwd)
        if restore_observer is not None:
            restore_observer()
        if context is not None and guard is not None:
            # Remove exactly our in-memory guard; preserve all native peer hooks.
            context._manager._hooks["pre_tool_call"].remove(guard)
        if agent is not None and agent.client is not None:
            agent.client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("CG_SMOKE_BASE_URL", "http://127.0.0.1:8080"),
    )
    parser.add_argument("--model", default=os.environ.get("CG_SMOKE_MODEL"))
    parser.add_argument("--hermes-root", type=Path, default=os.environ.get("CG_SMOKE_HERMES_ROOT"))
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--native-backend-python", type=Path)
    parser.add_argument("--native-ollama-url", default="http://127.0.0.1:11434/v1")
    parser.add_argument("--restart-project")
    parser.add_argument("--docker-context")
    parser.add_argument("--compose-file", type=Path, default=ROOT / "compose.yaml")
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--compression-url", default="http://127.0.0.1:11434/v1")
    parser.add_argument(
        "--reasoning-effort",
        choices=["none", "low", "medium", "high"],
        default=os.environ.get("CG_SMOKE_REASONING_EFFORT"),
    )
    args = parser.parse_args()
    if not args.model or args.hermes_root is None:
        parser.error("Set CG_SMOKE_MODEL and CG_SMOKE_HERMES_ROOT or pass explicit flags")
    from urllib.parse import urlsplit

    base = args.base_url.rstrip("/")
    url = urlsplit(base)
    if url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost"} or url.path:
        parser.error(
            "Smoke is restricted to a local HTTP production endpoint without URL credentials"
        )
    if url.username or url.password or url.query or url.fragment:
        parser.error("Credentials/query/fragment do not belong in smoke URLs")
    if args.native_backend_python:
        if args.restart_project or base != "http://127.0.0.1:8000":
            parser.error(
                "Native fallback requires explicit base127.0.0.1:8000 and no Compose restart"
            )
        endpoint = urlsplit(args.native_ollama_url)
        if (
            endpoint.scheme != "http"
            or endpoint.hostname not in {"127.0.0.1", "localhost"}
            or endpoint.path != "/v1"
            or endpoint.username
            or endpoint.password
            or endpoint.query
            or endpoint.fragment
        ):
            parser.error("Native fallback requires explicit local external Ollama /v1 URL")
    token = os.environ.get("CG_API_TOKEN", "")
    compression_url = args.compression_url.rstrip("/") if args.compress else None
    if compression_url:
        endpoint = urlsplit(compression_url)
        if (
            endpoint.scheme != "http"
            or endpoint.hostname not in {"127.0.0.1", "localhost"}
            or endpoint.path != "/v1"
            or endpoint.username
            or endpoint.password
            or endpoint.query
            or endpoint.fragment
        ):
            parser.error(
                "Native compression requires the explicitly local external Ollama /v1 endpoint"
            )
    restart = (
        owned_restart(base, token, args.restart_project, args.compose_file, args.docker_context)
        if args.restart_project
        else None
    )
    work = (args.work_dir or ROOT / ".venv" / ("hermes-smoke-" + uuid.uuid4().hex[:12])).resolve()
    if work.exists():
        raise SmokeFailure("Smoke requires a new dedicated work directory")
    work.mkdir(parents=True, exist_ok=False)
    native = None
    native_direct = native_target = None
    try:
        if args.native_backend_python:
            native = NativeBackend(
                args.native_backend_python,
                work,
                base,
                args.native_ollama_url.rstrip("/"),
                token,
            )
            native.start(initial=True)
            restart = native.restart
            from scripts.smoke_compose import direct_smoke, performance_smoke

            native_direct = direct_smoke(base, args.model, require_nginx=False)
            native_target = performance_smoke(base, args.model, args.reasoning_effort)
        models, _ = exchange(base, "/v1/models", token)
        if "ollama/" + args.model not in {row["id"] for row in models["data"]}:
            raise SmokeFailure("Explicit physical smoke model not available through production API")
        # Environment credentials are removed by isolated startup. Capture only the
        # user-supplied local API token above; never load installed Hermes dotenv.
        cases = [
            run_case(
                base,
                args.model,
                args.hermes_root.resolve(),
                work / "json",
                token,
                False,
                args.reasoning_effort,
                restart,
                compression_url,
            )
        ]
        cases.append(
            run_case(
                base,
                args.model,
                args.hermes_root.resolve(),
                work / "sse",
                token,
                True,
                args.reasoning_effort,
            )
        )
        report = {
            "result": "executed real Hermes smoke passed",
            "base_url": base,
            "native_platform": platform.system(),
            "cases": cases,
            "fixtures_retained": str(work),
            "scope": (
                "Real JSON/SSE/two-owner serialized continuation/replay/literal cg/synthesis; "
                "restart/compression are measured only when requested"
            ),
            "waiting_restart_gate": "EXECUTED" if restart else "OPEN",
            "compression_gate": "EXECUTED" if compression_url else "OPEN",
            "native_backend": None
            if native is None
            else {
                "python": str(native.python),
                "production_source_hashes": native.sources,
                "data_directory": str(native.data),
                "direct": native_direct,
                "target_measurements": native_target,
                "container_nginx_windows_wsl2_gate": "OPEN; native proof only",
            },
        }
        (work / "evidence.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
    finally:
        if native is not None:
            native.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — SDK errors may contain credentials; report type only.
        # Upstream/SDK exceptions may contain request data; report their type only.
        print(
            f"Hermes smoke FAILED ({type(exc).__name__}); gate remains OPEN",
            file=sys.stderr,
        )
        if isinstance(exc, SmokeFailure):
            print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
