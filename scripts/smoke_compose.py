"""Real, isolated Compose smoke. Fail closed; retain the owned data volume."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CommandFailure(RuntimeError):
    def __init__(self, command: list[str], exit_code: int):
        super().__init__(f"Command failed (exit {exit_code}): {' '.join(command)}")
        self.exit_code = exit_code


def run(command: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        command, cwd=ROOT, check=False, stdin=subprocess.DEVNULL, capture_output=capture, text=True
    )
    if result.returncode:
        # Captured config may contain a token; never echo its output on failure.
        raise CommandFailure(command, result.returncode)
    return result.stdout.strip() if capture else ""


def request(
    base: str,
    path: str,
    *,
    body: dict | None = None,
    method: str | None = None,
    headers: dict | None = None,
    timeout: float = 310,
):
    request_headers = dict(headers or {})
    token = os.environ.get("CG_API_TOKEN")
    if token:
        request_headers["Authorization"] = "Bearer " + token
    encoded = None if body is None else json.dumps(body).encode()
    if encoded is not None:
        request_headers["Content-Type"] = "application/json"
    message = urllib.request.Request(
        base + path, data=encoded, headers=request_headers, method=method
    )
    return urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
        message, timeout=timeout
    )


def json_request(base: str, path: str, **kwargs):
    with request(base, path, **kwargs) as response:
        return json.load(response)


def wait_ready(base: str, *, seconds: float = 90) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            health = json_request(base, "/health/ready", timeout=3)
            if health["storage_ready"]:
                return
        except (OSError, urllib.error.URLError, KeyError):
            pass
        time.sleep(0.5)
    raise RuntimeError("Storage/recovery readiness did not become healthy")


def collect_sse(base: str, path: str, *, trace: dict | None = None, **kwargs) -> list[dict]:
    data = []
    done = False
    started = time.monotonic()
    arrival_times = []
    heartbeats = 0
    with request(base, path, **kwargs) as response:
        if "text/event-stream" not in response.headers.get("Content-Type", ""):
            raise RuntimeError("Expected SSE content type")
        for raw in response:
            line = raw.decode().strip()
            if line.startswith(":"):
                heartbeats += 1
            if line == "event: error":
                raise RuntimeError("SSE emitted an error")
            if line == "data: [DONE]":
                done = True
                break
            if line.startswith("data: "):
                event = json.loads(line[6:])
                if "error" in event:
                    raise RuntimeError("SSE emitted an error envelope")
                data.append(event)
                arrival_times.append(time.monotonic() - started)
                if event.get("type") in {
                    "run.completed",
                    "run.failed",
                    "run.cancelled",
                }:
                    break
    if not data:
        raise RuntimeError("SSE produced no data")
    if path == "/v1/chat/completions" and not done:
        raise RuntimeError("Successful completion SSE did not end with DONE")
    if trace is not None:
        trace.update(
            {
                "first_data_seconds": arrival_times[0],
                "last_data_seconds": arrival_times[-1],
                "wall_seconds": time.monotonic() - started,
                "data_frames": len(data),
                "comment_heartbeats": heartbeats,
                "done": done,
                "x_accel_buffering": response.headers.get("X-Accel-Buffering"),
            }
        )
    return data


def passthrough(graph_id: str, model: str) -> dict:
    return {
        "schema_version": 1,
        "id": graph_id,
        "name": "Dedicated Compose smoke passthrough",
        "revision": 1,
        "base_model": model,
        "inputs": [{"id": "chat", "required": True}],
        "nodes": [
            {"id": "input", "type": "input", "input_id": "chat"},
            {"id": "output", "type": "output"},
        ],
        "edges": [
            {
                "id": "io",
                "source": "input",
                "target": "output",
                "target_port": "answer",
                "kind": "forward",
            }
        ],
        "loops": [],
        "output_node_id": "output",
    }


def assert_completion(response: dict, *, phase: str = "final JSON") -> None:
    choice = response["choices"][0]
    if response["object"] != "chat.completion" or choice["finish_reason"] != "stop":
        raise RuntimeError(
            f"Expected a successful final JSON completion ({phase}); "
            f"object={response['object']}, finish={choice['finish_reason']}, "
            f"visible_chars={len(choice['message'].get('content') or '')}"
        )
    if not choice["message"].get("content"):
        raise RuntimeError("Final JSON completion has no content")


def application_smoke(base: str, model: str, report: dict | None = None) -> tuple[str, str]:
    wait_ready(base)
    with request(base, "/", timeout=5) as response:
        if b"<html" not in response.read().lower():
            raise RuntimeError("Production UI did not serve HTML")
    health = json_request(base, "/health/ready", timeout=5)
    if not health["ollama_available"]:
        raise RuntimeError("Actual backend reports external Ollama unavailable")
    models = json_request(base, "/v1/models", timeout=10)
    if "ollama/" + model not in {row["id"] for row in models["data"]}:
        raise RuntimeError("Explicit smoke model is not installed upstream")
    graph_id = "smoke-" + uuid.uuid4().hex[:20]
    graph = passthrough(graph_id, model)
    created = json_request(base, "/api/graphs", body=graph)
    json_request(base, f"/api/graphs/{graph_id}/publish", body={"expected_revision": 1})
    if "cg/" + graph_id not in {row["id"] for row in json_request(base, "/v1/models")["data"]}:
        raise RuntimeError("Published virtual model not listed")
    body = {
        "model": "cg/" + graph_id,
        "messages": [{"role": "user", "content": "SMOKE_OK"}],
    }
    assert_completion(json_request(base, "/v1/chat/completions", body=body))
    chunks = collect_sse(base, "/v1/chat/completions", body={**body, "stream": True})
    if not any(c.get("choices") and c["choices"][0].get("finish_reason") == "stop" for c in chunks):
        raise RuntimeError("Graph SSE has no valid stop chunk")
    started = json_request(
        base,
        "/api/runs",
        body={"graph_id": graph_id, "revision": 1, "inputs": {"chat": "DURABLE_SMOKE"}},
    )
    run_id = started["run_id"]
    deadline = time.monotonic() + 30
    while True:
        detail = json_request(base, f"/api/runs/{run_id}")
        status = detail["run"]["status"]
        if status == "completed":
            break
        if status in {"failed", "cancelled", "interrupted"} or time.monotonic() > deadline:
            raise RuntimeError("Dedicated durable run did not complete")
        time.sleep(0.1)
    snapshot_hash = detail["run"]["graph_hash"]
    events = collect_sse(base, f"/api/runs/{run_id}/events")
    ids = [event["event_id"] for event in events]
    if ids != sorted(set(ids)):
        raise RuntimeError("Nonmonotonic persisted event IDs")
    if len(ids) > 1:
        replay = collect_sse(
            base, f"/api/runs/{run_id}/events", headers={"Last-Event-ID": str(ids[-2])}
        )
        if any(event["event_id"] <= ids[-2] for event in replay):
            raise RuntimeError("Last-Event-ID replay did not honor its cursor")
    graph = {**created, "name": "Edited after immutable smoke run"}
    json_request(
        base,
        f"/api/graphs/{graph_id}",
        method="PUT",
        body={"graph": graph, "expected_revision": 1},
    )
    unchanged = json_request(base, f"/api/runs/{run_id}")
    if unchanged["run"]["graph_hash"] != snapshot_hash or unchanged["snapshot"]["revision"] != 1:
        raise RuntimeError("Editing a draft changed a captured run snapshot")
    direct = direct_smoke(base, model)
    if report is not None:
        report["direct"] = direct
    return run_id, snapshot_hash


def direct_smoke(base: str, model: str, *, require_nginx: bool = True) -> dict:
    """Real public physical-model exchange; never execute the fixture function."""
    direct = {
        "model": "ollama/" + model,
        "messages": [{"role": "user", "content": "Reply with one short greeting."}],
        "max_tokens": 2048,
    }
    observations = []

    def checked_json(body, phase):
        began = time.monotonic()
        response = json_request(base, "/v1/chat/completions", body=body)
        choice = response["choices"][0]
        metadata = {
            "phase": phase,
            "object": response["object"],
            "finish": choice["finish_reason"],
            "visible_chars": len(choice["message"].get("content") or ""),
            "tool_calls": len(choice["message"].get("tool_calls") or []),
            "wall_seconds": round(time.monotonic() - began, 3),
        }
        observations.append(metadata)
        print(json.dumps({"direct_phase": metadata}), flush=True)
        return response

    ordinary = checked_json(direct, "ordinary JSON")
    assert_completion(ordinary, phase="ordinary JSON")
    multiturn = {
        **direct,
        "messages": [
            *direct["messages"],
            ordinary["choices"][0]["message"],
            {"role": "user", "content": "Now respond with a brief farewell."},
        ],
    }
    assert_completion(checked_json(multiturn, "multiturn JSON"), phase="multiturn JSON")
    direct_trace = {}
    direct_chunks = collect_sse(
        base,
        "/v1/chat/completions",
        trace=direct_trace,
        body={**multiturn, "stream": True},
    )
    if not any(
        c.get("choices") and c["choices"][0].get("finish_reason") == "stop" for c in direct_chunks
    ):
        raise RuntimeError("Direct SSE has no valid stop chunk")
    if require_nginx and direct_trace["x_accel_buffering"] != "no":
        raise RuntimeError("Production Nginx did not expose its disabled SSE buffering header")
    tool_body = {
        **direct,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Call smoke_probe exactly once with value SMOKE_OK. "
                    "After receiving its tool result, report that result briefly "
                    "and finish without requesting any further tool calls."
                ),
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "smoke_probe",
                    "description": "Pure smoke fixture; no executor or side effect.",
                    "parameters": {
                        "type": "object",
                        "properties": {"value": {"type": "string"}},
                        "required": ["value"],
                        "additionalProperties": False,
                    },
                },
            }
        ],
        "tool_choice": {"type": "function", "function": {"name": "smoke_probe"}},
        "parallel_tool_calls": False,
    }
    tool_response = checked_json(tool_body, "native tool JSON")
    tool_choice = tool_response["choices"][0]
    if tool_choice["finish_reason"] != "tool_calls":
        raise RuntimeError("Direct JSON did not preserve native function tool delivery")
    calls = tool_choice["message"]["tool_calls"]
    if len(calls) != 1 or calls[0]["function"]["name"] != "smoke_probe":
        raise RuntimeError("Direct JSON changed the forced native function")
    if not isinstance(json.loads(calls[0]["function"]["arguments"])["value"], str):
        raise TypeError("Direct JSON changed native JSON arguments")
    result_body = {
        **tool_body,
        "tool_choice": "auto",
        "messages": [
            *tool_body["messages"],
            tool_choice["message"],
            {
                "role": "tool",
                "tool_call_id": calls[0]["id"],
                "name": "smoke_probe",
                "content": "SMOKE_OK",
            },
        ],
    }
    assert_completion(checked_json(result_body, "native result JSON"), phase="native result JSON")
    tool_chunks = collect_sse(base, "/v1/chat/completions", body={**tool_body, "stream": True})
    if not any(
        c.get("choices") and c["choices"][0].get("finish_reason") == "tool_calls"
        for c in tool_chunks
    ):
        raise RuntimeError("Direct SSE did not preserve native tool finish reason")
    pieces = {}
    for chunk in tool_chunks:
        for choice in chunk.get("choices", []):
            for call in choice.get("delta", {}).get("tool_calls", []) or []:
                record = pieces.setdefault(call["index"], {"id": "", "name": "", "arguments": ""})
                record["id"] += call.get("id") or ""
                for field in ("name", "arguments"):
                    record[field] += call.get("function", {}).get(field) or ""
    if set(pieces) != {0} or pieces[0]["name"] != "smoke_probe":
        raise RuntimeError("Direct SSE changed native indexed function fragments")
    json.loads(pieces[0]["arguments"])
    sse_result = {
        **result_body,
        "stream": True,
        "messages": [
            *tool_body["messages"],
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": pieces[0]["id"],
                        "type": "function",
                        "function": {
                            "name": pieces[0]["name"],
                            "arguments": pieces[0]["arguments"],
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": pieces[0]["id"],
                "name": "smoke_probe",
                "content": "SMOKE_OK",
            },
        ],
    }
    resumed_chunks = collect_sse(base, "/v1/chat/completions", body=sse_result)
    if not any(
        c.get("choices") and c["choices"][0].get("finish_reason") == "stop" for c in resumed_chunks
    ):
        raise RuntimeError("Direct native SSE tool result did not complete with stop")
    try:
        json_request(
            base,
            "/v1/chat/completions",
            body={**direct, "model": "ollama/cg-smoke-unknown-" + uuid.uuid4().hex},
        )
    except urllib.error.HTTPError as error:
        if error.code != 404 or json.load(error)["error"]["code"] != "unknown_model":
            raise RuntimeError(
                "Unknown physical model did not return the contracted error"
            ) from None
    else:
        raise RuntimeError("Unknown physical model was silently replaced")
    return {
        "physical_model": model,
        "ordinary_json": True,
        "multiturn_json_sse": True,
        "native_tool_request_result_json_sse": True,
        "tools_executed": 0,
        "http_inference_exchanges": 7,
        "json_phase_metadata": observations,
        "unknown_model_404": True,
        "sse_chunks": len(direct_chunks),
        "direct_sse_arrival": direct_trace,
        "tool_sse_chunks": len(tool_chunks),
        "resumed_sse_chunks": len(resumed_chunks),
        "raw_arguments_sha256": hashlib.sha256(
            calls[0]["function"]["arguments"].encode()
        ).hexdigest(),
    }


def performance_smoke(base: str, model: str, effort: str | None) -> dict:
    """Target-hardware evidence; report measurements without promising a speedup."""
    results = []
    for sequential in (False, True):
        graph_id = ("sequential-" if sequential else "diamond-") + uuid.uuid4().hex[:16]
        generation = {"temperature": 0.0, "max_tokens": 2048}
        if effort:
            generation["reasoning_effort"] = effort
        graph = passthrough(graph_id, model)
        graph["name"] = "Dedicated same-model target measurement"
        graph["nodes"][1:1] = [
            {
                "id": node,
                "type": "llm",
                "tools_enabled": False,
                "generation": generation,
                "system_prompt": "Return exactly one short sentence about local graph computation.",
            }
            for node in ("left", "right", "final")
        ]
        graph["edges"] = [
            {
                "id": "i-l",
                "source": "input",
                "target": "left",
                "target_port": "question",
                "kind": "forward",
            },
            {
                "id": "r-input",
                "source": "left" if sequential else "input",
                "target": "right",
                "target_port": "question",
                "kind": "forward",
            },
            {
                "id": "l-f",
                "source": "left",
                "target": "final",
                "target_port": "left",
                "kind": "forward",
            },
            {
                "id": "r-f",
                "source": "right",
                "target": "final",
                "target_port": "right",
                "kind": "forward",
            },
            {
                "id": "f-o",
                "source": "final",
                "target": "output",
                "target_port": "answer",
                "kind": "forward",
            },
        ]
        json_request(base, "/api/graphs", body=graph)
        json_request(base, f"/api/graphs/{graph_id}/publish", body={"expected_revision": 1})
        started = time.monotonic()
        run_id = json_request(
            base,
            "/api/runs",
            body={
                "graph_id": graph_id,
                "revision": 1,
                "inputs": {"chat": "Describe local graph computation briefly."},
            },
        )["run_id"]
        deadline = started + 900
        while True:
            detail = json_request(base, f"/api/runs/{run_id}")
            if detail["run"]["status"] == "completed":
                break
            if (
                detail["run"]["status"] in {"failed", "cancelled", "interrupted"}
                or time.monotonic() >= deadline
            ):
                raise RuntimeError(
                    "Target graph measurement failed or exceeded its bounded900seconds"
                )
            time.sleep(0.2)
        nodes = {}
        for activation in detail["activations"]:
            if activation["node_id"] in {"left", "right", "final"}:
                began = datetime.fromisoformat(activation["started_at"])
                ended = datetime.fromisoformat(activation["ended_at"])
                nodes[activation["node_id"]] = {
                    "started_at": began.isoformat(),
                    "ended_at": ended.isoformat(),
                    "duration_seconds": (ended - began).total_seconds(),
                }
        if (
            set(nodes) != {"left", "right", "final"}
            or detail["run"]["upstream_attempts"] != 3
            or detail["run"]["node_executions"] != 3
        ):
            raise RuntimeError("Target measurement did not perform exactly three real model calls")
        results.append(
            {
                "shape": "sequential" if sequential else "diamond",
                "run_id": run_id,
                "graph_id": graph_id,
                "wall_seconds": round(time.monotonic() - started, 3),
                "queue_seconds": detail["run"]["queue_seconds"],
                "node_executions": detail["run"]["node_executions"],
                "upstream_attempts": detail["run"]["upstream_attempts"],
                "nodes": nodes,
            }
        )
    return {
        "physical_model": model,
        "generation": generation,
        "results": results,
        "interpretation": (
            "Single target measurement per shape; node spans include provider admission. "
            "Ollama may serialize GPU computation; no speedup promise."
        ),
    }


CONTAINER_PROBE = r"""
import hashlib,importlib.metadata,json,os,pathlib,sqlite3,tempfile,urllib.request
assert os.geteuid() == 10001
root=pathlib.Path(os.environ['CG_DATA_DIR'])
with tempfile.NamedTemporaryFile(prefix='.cg-smoke-',dir=root) as marker:
    marker.write(b'owned smoke permission marker'); marker.flush(); os.fsync(marker.fileno())
databases=[p for p in root.iterdir() if p.is_file() and p.suffix in ('.db','.sqlite','.sqlite3')]
assert len(databases)==1, 'Expected one production SQLite database'
with sqlite3.connect(databases[0].as_uri()+'?mode=ro',uri=True) as connection:
    assert connection.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
    assert connection.execute('PRAGMA quick_check').fetchone()[0]=='ok'
evidence={'uid':os.geteuid(),'python':__import__('sys').version.split()[0],
 'sqlite':sqlite3.sqlite_version,'journal_mode':'wal','quick_check':'ok',
 'actual_container_upstream':os.environ['OLLAMA_BASE_URL'],
 'sources':{n:hashlib.sha256((pathlib.Path('/app/app')/n).read_bytes()).hexdigest()
 for n in ['main.py','runtime/engine.py','storage/repository.py','providers/ollama.py',
 'providers/sse.py','tools/bridge.py','contracts/api.py','contracts/interfaces.py','contracts/config.py']},
 'packages':{n:importlib.metadata.version(n)
 for n in ['fastapi','httpx','jsonschema','pydantic','uvicorn']}}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
upstream=os.environ['OLLAMA_BASE_URL'].removesuffix('/v1')
exit_code=0
try:
    with opener.open(os.environ['OLLAMA_BASE_URL']+'/models',timeout=8) as response:
        assert json.load(response)['object']=='list'
    with opener.open(upstream+'/api/version',timeout=8) as response:
        evidence['ollama_version']=json.load(response)['version']
    with opener.open(upstream+'/api/tags',timeout=8) as response:
        evidence['models']=[{'name':m['name'],'digest':m['digest']}
                            for m in json.load(response)['models']]
    evidence['route_gate']='EXECUTED'
except Exception as error:
    evidence['route_gate']='OPEN; actual application-container route failed'
    evidence['error_type']=type(error).__name__
    reason=getattr(error,'reason',None)
    evidence['reason_type']=type(reason).__name__ if reason is not None else None
    evidence['errno']=getattr(reason,'errno',getattr(error,'errno',None))
    exit_code=1
path=root/'container-probe.json'
with path.open('x',encoding='utf-8') as file: json.dump(evidence,file,indent=2)
print(json.dumps(evidence),flush=True)
raise SystemExit(exit_code)
"""


PERSISTENCE_PROBE = r"""
import asyncio,hashlib,json,os,pathlib,sqlite3,threading
from datetime import datetime,timezone,timedelta
from app.contracts.api import ToolResult
from app.contracts.errors import CGError
from app.contracts.graph import Graph
from app.contracts.interfaces import (ActivationKey,ActivationRecord,ContinuationRoute,
    GraphSnapshot,PendingTool,ResponseEnvelope,RunContext,RunPolicy,RunSubmission,
    ToolBatch,ToolCheckpoint,canonical_arguments_hash,canonical_json,raw_text_hash)
from app.graphs.repository import FileGraphRepository
from app.graphs.validator import GraphValidator
from app.storage.repository import SQLiteRunRepository

async def rejected(operation):
    try: await operation
    except CGError: return
    raise AssertionError('Expected a durable guard to reject the operation')

async def probe():
    assert os.geteuid()==10001
    root=pathlib.Path('/data')
    assert not (root/'evidence.json').exists(), 'Refuse prior fixture state'
    now=datetime.now(timezone.utc)
    graph=Graph.model_validate({'schema_version':1,'id':'persist',
        'name':'Owned persistence fixture',
        'revision':1,'base_model':'no-inference','inputs':[{'id':'chat','required':True}],
        'nodes':[{'id':'i','type':'input','input_id':'chat'},
                 {'id':'owner','type':'llm','system_prompt':'No inference is performed',
                  'tools_enabled':True,'generation':{}},{'id':'o','type':'output'}],
        'edges':[{'id':'io','source':'i','target':'owner','target_port':'question','kind':'forward'},
                 {'id':'oo','source':'owner','target':'o','target_port':'answer','kind':'forward'}],
        'loops':[],'output_node_id':'o'})
    snapshot=GraphSnapshot.from_graph(graph)
    submission=RunSubmission(plan=GraphValidator().compile(snapshot),
        context=RunContext(namespace='anonymous',messages_json='[]',tools_json='[]'),
        inputs_json='{"chat":"fixture"}',policy=RunPolicy(client_request_json='{"model":"cg/persist"}',
            max_node_executions=10,max_tool_rounds=5,active_timeout_seconds=100,
            tool_wait_timeout_seconds=300))
    store=SQLiteRunRepository(root/'runs.sqlite')
    await store.initialize()
    def database_facts():
        return {'thread':threading.current_thread().name,'thread_id':threading.get_ident(),
                **{name:store.connection.execute('PRAGMA '+name).fetchone()[0]
                   for name in ['journal_mode','foreign_keys','synchronous','busy_timeout']}}
    facts=await store._call(database_facts)
    assert facts['journal_mode']=='wal' and facts['foreign_keys']==1 and facts['synchronous']==2
    assert facts['thread_id']!=threading.get_ident() and facts['thread'].startswith('cg-sqlite')
    assert await store._call(lambda:threading.get_ident())==facts['thread_id']
    try: store.connection.execute('SELECT 1')
    except sqlite3.ProgrammingError: pass
    else: raise AssertionError('SQLite connection escaped its dedicated thread')
    await store.create_run(submission,'r',now)
    cp=await store.load_checkpoint('r','anonymous')
    key=ActivationKey(run_id='r',scope_key='',iteration=0,node_id='owner')
    owner=ActivationRecord(activation_id='owner',key=key,status='ready',inputs=(),messages_json='[]')
    proposed=cp.model_copy(update={'activations':(owner,),
        'run':cp.run.model_copy(update={'status':'running','started_at':now})})
    await store.save_checkpoint(proposed,cp.run.state_version)
    await rejected(store.save_checkpoint(proposed,cp.run.state_version))
    cp=await store.load_checkpoint('r','anonymous')
    await rejected(store.save_checkpoint(cp.model_copy(update={'activations':
        (owner,owner.model_copy(update={'activation_id':'duplicate'}))}),cp.run.state_version))
    assert await store.load_checkpoint('r','anonymous')==cp
    claims=await asyncio.gather(*[store.claim_activation(key,value,now)
                                 for value in ['first','second']])
    assert sum(value is not None for value in claims)==1
    cp=await store.load_checkpoint('r','anonymous')
    assert cp.run.node_executions==1 and cp.run.upstream_attempts==1
    owner=cp.activations[0].model_copy(update={'status':'waiting_tools','provider_round':1})
    mappings=tuple(PendingTool(external_id=id_,run_id='r',activation_id='owner',node_id='owner',
        provider_round=1,call_ordinal=index,internal_id='same',name='fixture',arguments='{}',
        arguments_hash=raw_text_hash('{}'),canonical_arguments_hash=canonical_arguments_hash('{}'),
        status='unexposed') for index,id_ in enumerate(('cg_a','cg_b')))
    await store.save_checkpoint(cp.model_copy(update={'activations':(owner,),
        'pending_tools':mappings}),cp.run.state_version)
    cp=await store.load_checkpoint('r','anonymous')
    def envelope(sequence,batch=None,calls=None):
        message={'role':'assistant','content':'answer'} if calls is None else {
            'role':'assistant','content':None,'tool_calls':calls}
        return ResponseEnvelope(run_id='r',batch_id=batch,response_sequence=sequence,
            completion_json=canonical_json({'id':'completion-'+str(sequence),'created':1,
                'model':'cg/persist','choices':[{'index':0,'message':message,
                'finish_reason':'stop' if calls is None else 'tool_calls'}]}))
    response=envelope(1,'b',[{'id':id_,'type':'function','function':{'name':'fixture','arguments':'{}'}}
                            for id_ in ('cg_a','cg_b')])
    batch=ToolBatch(batch_id='b',run_id='r',sequence=1,status='open',external_ids=('cg_a','cg_b'),
        prepared_at=now,expires_at=now+timedelta(seconds=300),envelope=response)
    exposed=cp.model_copy(update={'run':cp.run.model_copy(update={'status':'waiting_tools'}),
        'pending_tools':tuple(tool.model_copy(update={'status':'pending','batch_id':'b'})
                              for tool in mappings),
        'batches':(batch,),'responses':(response,)})
    await store.checkpoint_batch(ToolCheckpoint(checkpoint=exposed,batch=batch),
                                 cp.run.state_version)
    def route(id_,content):
        return ContinuationRoute(namespace='anonymous',model='cg/persist',run_id='r',batch_id='b',
            results=(ToolResult(tool_call_id=id_,content=content),))
    stale=await store.load_checkpoint('r','anonymous')
    first,duplicate=await asyncio.gather(*[store.accept_results(route('cg_a','first'),
        raw_text_hash('partial'),now) for _ in range(2)])
    assert {first.kind,duplicate.kind}=={'partial','joined'}
    assert first.claim.claim_id==duplicate.claim.claim_id
    await rejected(store.save_checkpoint(stale,stale.run.state_version))
    await rejected(store.accept_results(route('cg_a','changed'),raw_text_hash('changed'),now))
    second=await store.accept_results(route('cg_b','second'),raw_text_hash('complete'),now)
    assert second.kind=='ready'
    cp=await store.load_checkpoint('r','anonymous')
    assert [tool.result for tool in cp.pending_tools]==['first','second']
    assert cp.batches[0].expires_at==batch.expires_at and cp.run.tool_rounds==1
    final=envelope(2)
    owner=cp.activations[0].model_copy(update={'status':'completed','ended_at':now,'payload_json':'"answer"'})
    output=ActivationRecord(activation_id='output',key=ActivationKey(
        run_id='r',scope_key='',iteration=0,node_id='o'),status='completed',
        inputs=(),messages_json='[]',ended_at=now,payload_json='"answer"')
    completed=cp.model_copy(update={'run':cp.run.model_copy(update={
        'status':'completed','ended_at':now,'output_json':'"answer"'}),
        'activations':(owner,output),'responses':cp.responses+(final,)})
    original=store._seal_claims
    def fail_seal(*args): raise RuntimeError('Owned fault injection before claim seal')
    store._seal_claims=fail_seal
    try: await store.complete_run(completed,final,cp.run.state_version)
    except RuntimeError: pass
    else: raise AssertionError('Expected transaction fault')
    assert await store.load_checkpoint('r','anonymous')==cp
    assert (await store.get_claim(first.claim.claim_id)).status=='pending'
    store._seal_claims=original
    await store.complete_run(completed,final,cp.run.state_version)
    for accepted in (first,second):
        assert (await store.get_claim(accepted.claim.claim_id)).envelope==final
    def fk_failure():
        def insert(): store.connection.execute("INSERT INTO events VALUES('orphan',1,'{}')")
        store._transaction(insert)
    await rejected(store._call(fk_failure))
    foreign=await store._call(lambda:store.connection.execute(
        'PRAGMA foreign_key_check').fetchall())
    assert foreign==[]
    await store.close()
    store=SQLiteRunRepository(root/'runs.sqlite')
    await store.initialize()
    recovered=await store.load_checkpoint('r','anonymous')
    assert recovered.run.status=='completed'
    assert recovered.run.snapshot.graph_hash==snapshot.graph_hash
    replay=await store.accept_results(route('cg_a','first'),raw_text_hash('partial'),now)
    assert replay.kind=='replay' and replay.claim.envelope==final
    await rejected(store.accept_results(route('cg_a','first'),raw_text_hash('new'),now))
    events=await store.read_events('r','anonymous',0)
    assert [event.event_id for event in events]==list(range(1,len(events)+1))
    integrity=await store._call(lambda:store.connection.execute('PRAGMA quick_check').fetchone()[0])
    assert integrity=='ok'
    await store.close()
    files=FileGraphRepository(root/'files',GraphValidator())
    await files.create(graph)
    publication=await files.publish('persist',1)
    graph2=graph.model_copy(update={'name':'Changed draft'})
    await files.save(graph2,1)
    assert (await files.load_snapshot('persist',1)).graph_hash==publication.graph_hash
    before=(root/'files/graphs/persist.json').read_bytes()
    original_fsync=os.fsync
    def fail_fsync(fd): raise OSError('Owned file-sync fault')
    os.fsync=fail_fsync
    try: await rejected(files.save((await files.get('persist')),2))
    finally: os.fsync=original_fsync
    assert (root/'files/graphs/persist.json').read_bytes()==before
    outside=root/'symlink-target'
    outside.mkdir()
    target=outside/'target.json'
    target.write_text('owned marker')
    (root/'files/graphs/linked.json').symlink_to(target)
    await rejected(files.get('linked'))
    linked_root=root/'linked-files'
    linked_root.mkdir()
    (linked_root/'graphs').symlink_to(outside,target_is_directory=True)
    await rejected(FileGraphRepository(linked_root,GraphValidator()).create(graph))
    assert target.read_text()=='owned marker'
    await rejected(files.get('../escape'))
    descriptor=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)
    source_names=['contracts/api.py','contracts/graph.py','contracts/interfaces.py',
        'storage/repository.py','graphs/repository.py','graphs/validator.py']
    evidence={'result':'executed persistence probe passed','uid':os.geteuid(),
        'python':__import__('sys').version.split()[0],'sqlite':sqlite3.sqlite_version,'pragmas':facts,
        'graph_hash':snapshot.graph_hash,'tool_rounds':recovered.run.tool_rounds,
        'node_executions':recovered.run.node_executions,'upstream_attempts':recovered.run.upstream_attempts,
        'events':len(events),'quick_check':'ok','sources':{name:hashlib.sha256(
            (pathlib.Path('/app/app')/name).read_bytes()).hexdigest() for name in source_names},
        'checks':['thread-affinity','WAL/FK/FULL','CAS','activation uniqueness and claim',
            'partial duplicate race','changed-result conflict','fixed deadline/budget',
            'atomic response/claim fault rollback','claim seal','FK constraint',
            'close/reopen exact replay','immutable publication','file/directory fsync',
            'fsync-fault prior bytes','Linux file/directory symlink rejection','path traversal']}
    (root/'evidence.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence),flush=True)

asyncio.run(asyncio.wait_for(probe(),60))
"""


def persistence_smoke(docker: list[str], compose: list[str], project: str, volume: str) -> None:
    """Use the real service image/config with no network, ports or health probe."""
    override = """services:
  backend:
    network_mode: none
    ports: !reset []
    extra_hosts: !reset []
    restart: 'no'
    healthcheck:
      disable: true
    environment:
      CG_API_TOKEN: ''
"""
    run([*compose, "build", "backend"])
    name = project + "-persistence"
    encoded = base64.b64encode(PERSISTENCE_PROBE.encode()).decode()
    descriptor, parameter_name = tempfile.mkstemp(prefix="cg-compose-override-", suffix=".yaml")
    parameter_file = Path(parameter_name)
    try:
        # Close before Compose reads it: Windows prevents reading an open temp file.
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as parameter:
            parameter.write(override)
        command = [
            *compose,
            "-f",
            str(parameter_file),
            "run",
            "-d",
            "-T",
            "--no-deps",
            "--name",
            name,
            "--pull",
            "never",
            "--entrypoint",
            "python",
            "backend",
            "-c",
            "import base64;exec(base64.b64decode('" + encoded + "'))",
        ]
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            cwd=ROOT,
            check=False,
        )
    finally:
        # Delete only this newly created parameter file; retain all run evidence/data.
        parameter_file.unlink()
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        raise CommandFailure([*compose, "run", "<bounded persistence probe>"], result.returncode)
    container = result.stdout.strip()
    print(
        json.dumps(
            {
                "container": container,
                "name": name,
                "volume_retained": volume,
                "purpose": "production persistence only; no network/ports/server",
            }
        ),
        flush=True,
    )
    deadline = time.monotonic() + 90
    while True:
        state = json.loads(
            run(
                [*docker, "inspect", container, "--format", "{{json .State}}"],
                capture=True,
            )
        )
        if not state["Running"]:
            break
        if time.monotonic() >= deadline:
            run([*docker, "stop", "--time", "5", container])
            raise RuntimeError("Owned persistence probe exceeded90seconds; container stopped")
        time.sleep(0.25)
    metadata = json.loads(
        run(
            [*docker, "inspect", container, "--format", "{{json .HostConfig}}"],
            capture=True,
        )
    )
    assert metadata["NetworkMode"] == "none" and not metadata.get("PortBindings")
    assert metadata["ReadonlyRootfs"] and metadata["CapDrop"] == ["ALL"]
    assert "no-new-privileges:true" in metadata["SecurityOpt"]
    run([*docker, "logs", container])
    print(
        json.dumps(
            {
                "container": container,
                "exit_code": state["ExitCode"],
                "status": state["Status"],
                "volume_retained": volume,
                "network_mode": "none",
                "ports": [],
                "readonly_root": True,
                "cap_drop": ["ALL"],
                "probe_sha256": hashlib.sha256(PERSISTENCE_PROBE.encode()).hexdigest(),
            }
        ),
        flush=True,
    )
    if state["ExitCode"]:
        raise CommandFailure(["production-persistence-probe"], state["ExitCode"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", default=os.environ.get("DOCKER_CONTEXT"))
    parser.add_argument(
        "--project",
        default=os.environ.get("CG_SMOKE_PROJECT") or os.environ.get("COMPOSE_PROJECT_NAME"),
    )
    parser.add_argument("--file", action="append", dest="files")
    parser.add_argument("--model", default=os.environ.get("CG_SMOKE_MODEL"))
    parser.add_argument("--hermes-python", type=Path)
    parser.add_argument("--hermes-root", type=Path)
    parser.add_argument("--hermes-docker-context")
    parser.add_argument("--reasoning-effort", choices=["none", "low", "medium", "high"])
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--persistence-only", action="store_true")
    parser.add_argument("--direct-only", action="store_true")
    args = parser.parse_args()
    if bool(args.hermes_python) != bool(args.hermes_root):
        parser.error("Pass both --hermes-python and --hermes-root for the installed native client")
    if os.environ.get("CG_DATA_DIR", "/data") != "/data":
        parser.error("Compose fixes cg_data:/data; clear the native CG_DATA_DIR override")
    if not (args.validate_only or args.persistence_only) and not args.model:
        parser.error(
            "Supply --model or CG_SMOKE_MODEL; no model is installed/downloaded implicitly"
        )
    project = args.project or "cg-smoke-" + uuid.uuid4().hex[:12]
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", project):
        parser.error("Unsafe Compose project name")
    files = args.files or (
        os.environ["COMPOSE_FILE"].split(os.pathsep)
        if os.environ.get("COMPOSE_FILE")
        else [str(ROOT / "compose.yaml")]
    )
    files = [str(Path(file).resolve()) for file in files]
    docker = ["docker", *(["--context", args.context] if args.context else [])]
    context = run([*docker, "context", "show"], capture=True)
    target = run(
        [*docker, "version", "--format", "{{.Server.Os}}/{{.Server.Arch}}"],
        capture=True,
    )
    if not target.startswith("linux/"):
        raise RuntimeError("Compose delivery requires a Linux Docker daemon")
    compose = [*docker, "compose", "-p", project]
    for file in files:
        compose.extend(["-f", file])
    run([*compose, "config", "--quiet"])
    config = json.loads(run([*compose, "config", "--format", "json"], capture=True))
    if set(config["services"]) != {"backend", "frontend"}:
        raise RuntimeError("Smoke requires exactly backend/frontend; unexpected service/profile")
    if os.environ.get("COMPOSE_PROFILES"):
        raise RuntimeError(
            "Default delivery has no profiles; explicit COMPOSE_PROFILES is unsupported"
        )
    for service, port in (("backend", 8000), ("frontend", 8080)):
        ports = config["services"][service].get("ports", [])
        if (
            len(ports) != 1
            or ports[0].get("host_ip") != "127.0.0.1"
            or int(ports[0]["published"]) != port
        ):
            raise RuntimeError("Smoke only targets the specified loopback ports 8000/8080")
    mounts = config["services"]["backend"]["volumes"]
    if len(mounts) != 1 or mounts[0]["type"] != "volume" or mounts[0]["target"] != "/data":
        raise RuntimeError("Unexpected data mount; no host/tool/socket mounts allowed")
    if config["services"]["frontend"].get("volumes"):
        raise RuntimeError("Frontend smoke allows no host or data mounts")
    for service in config["services"].values():
        if service.get("privileged") or service.get("devices") or service.get("gpus"):
            raise RuntimeError("Smoke permits no privileged/device/GPU grants")
        if service.get("network_mode") == "host" or service.get("command"):
            raise RuntimeError("Smoke permits no host networking or application command override")
    backend_env = config["services"]["backend"]["environment"]
    if backend_env.get("CG_DATA_DIR") != "/data" or backend_env.get("WEB_CONCURRENCY") != "1":
        raise RuntimeError("Smoke requires /data and exactly one backend worker")
    volume = config["volumes"][mounts[0]["source"]]["name"]
    if volume != project + "_cg_data":
        raise RuntimeError("Smoke refuses a volume shared with another project")
    print(
        json.dumps(
            {
                "context": context,
                "project": project,
                "files": files,
                "profiles": [],
                "ports": [8000, 8080],
                "volume": volume,
                "target": target,
                "caller_platform": platform.system(),
            }
        ),
        flush=True,
    )
    if args.validate_only:
        print("Static configuration only; build/health/Ollama/durability remain OPEN")
        return
    if run(
        [
            *docker,
            "ps",
            "-aq",
            "--filter",
            f"label=com.docker.compose.project={project}",
        ],
        capture=True,
    ):
        raise RuntimeError("Smoke refuses an existing project's containers")
    if run([*docker, "volume", "ls", "-q", "--filter", f"name=^{volume}$"], capture=True):
        raise RuntimeError("Smoke refuses an existing data volume")
    if run(
        [
            *docker,
            "network",
            "ls",
            "-q",
            "--filter",
            f"label=com.docker.compose.project={project}",
        ],
        capture=True,
    ):
        raise RuntimeError("Smoke refuses an existing project's network")
    if args.persistence_only:
        persistence_smoke(docker, compose, project, volume)
        return
    for port in (8000, 8080):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    started = False
    primary_error = None
    try:
        run([*compose, "build"])
        started = True  # up may create resources even if it subsequently fails.
        run([*compose, "up", "-d", "--wait", "--wait-timeout", "120"])
        report = {
            "project": project,
            "context": context,
            "caller_platform": platform.system(),
        }
        probe_command = [
            *compose,
            "exec",
            "-T",
            "backend",
            "python",
            "-c",
            CONTAINER_PROBE,
        ]
        probe_result = subprocess.run(
            probe_command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        if probe_result.stdout.strip():
            report["actual_backend"] = json.loads(probe_result.stdout)
            print(
                json.dumps({"actual_application_container": report["actual_backend"]}),
                flush=True,
            )
        if probe_result.returncode:
            raise CommandFailure(
                [*compose, "exec", "-T", "backend", "<owned storage/upstream probe>"],
                probe_result.returncode,
            )
        expected_sources = {
            name: hashlib.sha256((ROOT / "backend/app" / name).read_bytes()).hexdigest()
            for name in report["actual_backend"]["sources"]
        }
        if report["actual_backend"]["sources"] != expected_sources:
            raise RuntimeError(
                "Actual backend image does not match current pinned production sources"
            )
        report["production_sources_match"] = True
        if args.direct_only:
            report["direct"] = direct_smoke("http://127.0.0.1:8080", args.model)
            print(
                json.dumps({"result": "bounded direct-only probe passed", "evidence": report}),
                flush=True,
            )
            return
        run_id, graph_hash = application_smoke("http://127.0.0.1:8080", args.model, report)
        run([*compose, "exec", "-T", "frontend", "nginx", "-V"])
        nginx_config = run(
            [
                *compose,
                "exec",
                "-T",
                "frontend",
                "nginx",
                "-T",
                "-c",
                "/tmp/nginx.conf",
            ],
            capture=True,
        )
        budget = max(
            int(backend_env[name])
            for name in (
                "CG_RUN_ACTIVE_TIMEOUT_SECONDS",
                "CG_TOOL_WAIT_TIMEOUT_SECONDS",
                "CG_LLM_TIMEOUT_SECONDS",
            )
        )
        timeouts = {}
        for setting in ("proxy_read_timeout", "proxy_send_timeout", "send_timeout"):
            match = re.search(r"\b" + setting + r"\s+(\d+)s;", nginx_config)
            if not match or int(match[1]) <= budget:
                raise RuntimeError(
                    "Actual Nginx timeout does not exceed server's independent budgets"
                )
            timeouts[setting] = int(match[1])
        if (
            "proxy_buffering off;" not in nginx_config
            or "proxy_request_buffering off;" not in nginx_config
        ):
            raise RuntimeError("Actual Nginx configuration buffers the streaming route")
        report["nginx"] = {
            "timeouts_seconds": timeouts,
            "server_budget_max_seconds": budget,
            "buffering": "off",
        }
        report["containers"] = {}
        for service in ("backend", "frontend"):
            container = run([*compose, "ps", "-q", service], capture=True)
            metadata = json.loads(
                run(
                    [
                        *docker,
                        "inspect",
                        container,
                        "--format",
                        (
                            '{"id":{{json .Id}},"image":{{json .Image}},'
                            '"user":{{json .Config.User}},'
                            '"readonly":{{json .HostConfig.ReadonlyRootfs}},'
                            '"caps":{{json .HostConfig.CapDrop}},'
                            '"security":{{json .HostConfig.SecurityOpt}}}'
                        ),
                    ],
                    capture=True,
                )
            )
            if (
                metadata["user"] != ("10001:10001" if service == "backend" else "101:101")
                or not metadata["readonly"]
                or metadata["caps"] != ["ALL"]
                or "no-new-privileges:true" not in metadata["security"]
            ):
                raise RuntimeError("Actual application container lacks expected non-root isolation")
            report["containers"][service] = metadata
        run([*compose, "restart", "backend"])
        wait_ready("http://127.0.0.1:8080")
        recovered = json_request("http://127.0.0.1:8080", f"/api/runs/{run_id}")
        if (
            recovered["run"]["status"] != "completed"
            or recovered["run"]["graph_hash"] != graph_hash
        ):
            raise RuntimeError("Restart did not preserve completed history and snapshot")
        report["completed_history_restart"] = {
            "run_id": run_id,
            "graph_hash": graph_hash,
        }
        # Recreate only this fresh smoke project's containers/network; retain its
        # named volume and assert the published graph/history survive a real up.
        run([*compose, "down", "--timeout", "45"])
        run([*compose, "up", "-d", "--wait", "--wait-timeout", "120"])
        recreated = json_request("http://127.0.0.1:8080", f"/api/runs/{run_id}")
        listed = json_request("http://127.0.0.1:8080", "/v1/models")
        if (
            recreated["run"]["status"] != "completed"
            or recreated["run"]["graph_hash"] != graph_hash
            or recreated["snapshot"]["revision"] != 1
            or "cg/" + recreated["run"]["graph_id"] not in {row["id"] for row in listed["data"]}
        ):
            raise RuntimeError(
                "Owned down/up did not preserve publication/history/immutable snapshot"
            )
        report["volume_preserving_recreate"] = {
            "run_id": run_id,
            "graph_hash": graph_hash,
            "volume": volume,
        }
        report["recreated_containers"] = {}
        for service in ("backend", "frontend"):
            container = run([*compose, "ps", "-q", service], capture=True)
            image = run([*docker, "inspect", container, "--format", "{{.Image}}"], capture=True)
            if (
                container == report["containers"][service]["id"]
                or image != report["containers"][service]["image"]
            ):
                raise RuntimeError(
                    "Owned recreation did not replace containers with the same tested images"
                )
            report["recreated_containers"][service] = {"id": container, "image": image}
        report["target_measurement"] = performance_smoke(
            "http://127.0.0.1:8080", args.model, args.reasoning_effort
        )
        if args.hermes_python:
            work = ROOT / ".venv" / ("hermes-production-" + uuid.uuid4().hex[:12])
            windows_interop = (
                platform.system() == "Linux"
                and bool(os.environ.get("WSL_DISTRO_NAME"))
                and args.hermes_python.suffix.lower() == ".exe"
            )
            native_context = args.hermes_docker_context or args.context

            def native_path(path):
                if windows_interop:
                    return run(["wslpath", "-w", str(Path(path).resolve())], capture=True)
                return str(Path(path).resolve())

            if windows_interop:
                if not args.hermes_docker_context:
                    raise RuntimeError(
                        "WSL Windows-native client requires explicit Hermes Docker context"
                    )
                metadata = json.loads(
                    run(
                        [
                            str(args.hermes_python.resolve()),
                            "-c",
                            "import importlib.metadata as m,json,platform,subprocess,sys;"
                            "from pathlib import Path;"
                            "sys.path.append(str(Path(sys.argv[2])/'venv'/'Lib'/'site-packages'));"
                            "print(json.dumps({'platform':platform.system(),'python':sys.version.split()[0],"
                            "'versions':{n:m.version(n) for n in "
                            "['hermes-agent','openai','httpx']},"
                            "'daemon_id':subprocess.check_output(['docker','--context',sys.argv[1],"
                            "'info','--format','{{.ID}}'],text=True).strip()}))",
                            native_context,
                            native_path(args.hermes_root),
                        ],
                        capture=True,
                    )
                )
                if (
                    metadata["platform"] != "Windows"
                    or metadata["python"] != "3.11.15"
                    or metadata["versions"]
                    != {"hermes-agent": "0.18.2", "openai": "2.24.0", "httpx": "0.28.1"}
                    or metadata["daemon_id"]
                    != run([*docker, "info", "--format", "{{.ID}}"], capture=True)
                ):
                    raise RuntimeError("WSL/native pinned client/daemon identity does not match")
                report["native_client_interop"] = metadata
            hermes_command = [
                str(args.hermes_python.resolve()),
                native_path(ROOT / "scripts/smoke_hermes.py"),
                "--model",
                args.model,
                "--hermes-root",
                native_path(args.hermes_root),
                "--work-dir",
                native_path(work),
                "--restart-project",
                project,
                "--compose-file",
                native_path(files[0]),
                "--compress",
            ]
            if len(files) != 1:
                raise RuntimeError(
                    "Native restart smoke currently requires one explicit Compose file"
                )
            if native_context:
                hermes_command.extend(["--docker-context", native_context])
            if args.reasoning_effort:
                hermes_command.extend(["--reasoning-effort", args.reasoning_effort])
            run(hermes_command)
            report["native_hermes"] = json.loads(
                (work / "evidence.json").read_text(encoding="utf-8")
            )
        else:
            report["native_hermes"] = {
                "gate": "OPEN",
                "reason": (
                    "Run with the pinned installed --hermes-python and --hermes-root; "
                    "no client is installed automatically"
                ),
            }
        encoded_report = base64.b64encode(json.dumps(report).encode()).decode()
        run(
            [
                *compose,
                "exec",
                "-T",
                "backend",
                "python",
                "-c",
                "import base64,pathlib;p=pathlib.Path('/data/delivery-smoke.json');"
                "assert not p.exists();p.write_bytes(base64.b64decode('" + encoded_report + "'))",
            ]
        )
        print(json.dumps(report), flush=True)
        print(
            json.dumps(
                {
                    "result": "executed smoke passed",
                    "run_id": run_id,
                    "graph_hash": graph_hash,
                    "volume_retained": volume,
                }
            ),
            flush=True,
        )
    except BaseException as error:  # noqa: BLE001 — preserve original failure through scoped teardown.
        primary_error = error
        if started:
            try:
                # Only the owned frontend startup log and health output are captured;
                # never dump container environments, auth headers or backend history.
                failure = {"project": project, "failure_type": type(error).__name__}
                failure["partial_evidence"] = locals().get("report")
                for service in ("backend", "frontend"):
                    container = run([*compose, "ps", "--all", "--quiet", service], capture=True)
                    if container:
                        failure[service] = json.loads(
                            run(
                                [*docker, "inspect", container, "--format", "{{json .State}}"],
                                capture=True,
                            )
                        )
                log = subprocess.run(
                    [*compose, "logs", "--no-color", "--no-log-prefix", "--tail", "60", "frontend"],
                    cwd=ROOT,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                failure["frontend_startup_log"] = log.stdout[-16000:]
                evidence = ROOT / ".venv" / ("compose-failure-" + project + ".json")
                with evidence.open("x", encoding="utf-8") as output:
                    json.dump(failure, output, indent=2)
                print(
                    json.dumps({"retained_failure": str(evidence), "evidence": failure}), flush=True
                )
            except (OSError, RuntimeError, ValueError) as capture_error:
                print(
                    "Failure evidence capture also failed ("
                    + type(capture_error).__name__
                    + "); original exit and scoped teardown preserved",
                    file=sys.stderr,
                )
    finally:
        if started:
            try:
                run([*compose, "down", "--timeout", "45"])
                containers = run(
                    [
                        *docker,
                        "ps",
                        "-aq",
                        "--filter",
                        f"label=com.docker.compose.project={project}",
                    ],
                    capture=True,
                )
                networks = run(
                    [
                        *docker,
                        "network",
                        "ls",
                        "-q",
                        "--filter",
                        f"label=com.docker.compose.project={project}",
                    ],
                    capture=True,
                )
                if containers or networks:
                    raise RuntimeError("Owned smoke container/network residue remains")
                retained = run(
                    [*docker, "volume", "ls", "-q", "--filter", f"name=^{volume}$"],
                    capture=True,
                )
                print(
                    json.dumps(
                        {
                            "residue_containers": [],
                            "residue_networks": [],
                            "retained_volume": retained,
                        }
                    ),
                    flush=True,
                )
            except BaseException:  # noqa: BLE001 — preserve prior failure and report cleanup.
                if primary_error is None:
                    # A pending direct-only return skips the shared raise below.
                    raise
                else:
                    print(
                        "Cleanup also failed; inspect the named owned project",
                        file=sys.stderr,
                    )
    if primary_error is not None:
        raise primary_error


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, TypeError, KeyError) as exc:
        print(f"Compose smoke FAILED: {exc}", file=sys.stderr)
        raise SystemExit(exc.exit_code if isinstance(exc, CommandFailure) else 1) from None
