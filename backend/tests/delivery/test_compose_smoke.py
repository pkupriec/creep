"""Exercise smoke lifecycle failures without Docker, sockets, HTTP or inference."""

import ast
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SMOKE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "smoke_compose.py"
PROJECT = "cg-test-cleanup"
VOLUME = PROJECT + "_cg_data"


@pytest.fixture
def smoke(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("compose_smoke", SMOKE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module.platform, "system", lambda: "Windows")
    (tmp_path / ".venv").mkdir()
    monkeypatch.setattr(module.os, "environ", {})
    monkeypatch.setattr(
        sys,
        "argv",
        [str(SMOKE_PATH), "--project", PROJECT, "--model", "fixture", "--direct-only"],
    )
    state = SimpleNamespace(
        commands=[],
        down_error=None,
        primary_error=None,
        residue=None,
        cleaned=False,
        direct_calls=0,
        application_calls=0,
        recreations=0,
    )
    config = {
        "services": {
            "backend": {
                "ports": [{"host_ip": "127.0.0.1", "published": 8000}],
                "volumes": [{"type": "volume", "target": "/data", "source": "cg_data"}],
                "environment": {
                    "CG_DATA_DIR": "/data",
                    "WEB_CONCURRENCY": "1",
                    "CG_RUN_ACTIVE_TIMEOUT_SECONDS": "1800",
                    "CG_TOOL_WAIT_TIMEOUT_SECONDS": "1800",
                    "CG_LLM_TIMEOUT_SECONDS": "1800",
                },
            },
            "frontend": {"ports": [{"host_ip": "127.0.0.1", "published": 8080}]},
        },
        "volumes": {"cg_data": {"name": VOLUME}},
    }

    def fake_run(command, *, capture=False):
        state.commands.append(command)
        if "compose" in command:
            operation = command[command.index("-f") + 2 :]
            if operation == ["config", "--quiet"]:
                return ""
            if operation == ["config", "--format", "json"]:
                return json.dumps(config)
            if operation == ["down", "--timeout", "45"]:
                state.cleaned = True
                if state.down_error:
                    raise module.CommandFailure(command, state.down_error)
                return ""
            if operation == ["up", "-d", "--wait", "--wait-timeout", "120"]:
                state.recreations += 1
                return ""
            if operation == ["build"] or operation == ["restart", "backend"]:
                return ""
            if operation[:3] == ["ps", "--all", "--quiet"]:
                return ""
            if operation[:2] == ["ps", "-q"]:
                return f"{operation[2]}-{state.recreations}"
            if operation[:3] == ["exec", "-T", "frontend"]:
                return (
                    "proxy_read_timeout 1860s; proxy_send_timeout 1860s; send_timeout 1860s;"
                    "proxy_buffering off; proxy_request_buffering off;"
                )
            if operation[:3] == ["exec", "-T", "backend"]:
                return ""
        elif command[1:] == ["context", "show"]:
            return "fixture-context"
        elif command[1] == "version":
            return "linux/amd64"
        elif command[1:3] == ["ps", "-aq"]:
            return "owned-container" if state.cleaned and state.residue == "container" else ""
        elif command[1:3] == ["network", "ls"]:
            return "owned-network" if state.cleaned and state.residue == "network" else ""
        elif command[1:3] == ["volume", "ls"]:
            return VOLUME if state.cleaned else ""
        elif command[1] == "inspect":
            if command[-1] == "{{.Image}}":
                return "fixture-image"
            return json.dumps(
                {
                    "id": command[2],
                    "image": "fixture-image",
                    "user": "10001:10001" if command[2].startswith("backend") else "101:101",
                    "readonly": True,
                    "caps": ["ALL"],
                    "security": ["no-new-privileges:true"],
                }
            )
        pytest.fail(f"Unexpected external command: {command}")

    def fake_subprocess(command, **kwargs):
        if command[-1] == module.CONTAINER_PROBE:
            return SimpleNamespace(stdout=json.dumps({"sources": {}}), returncode=0)
        if "logs" in command:
            return SimpleNamespace(stdout="fixture startup", returncode=0)
        pytest.fail(f"Unexpected subprocess: {command}")

    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def bind(self, address):
            assert address in [("127.0.0.1", 8000), ("127.0.0.1", 8080)]

    def fake_direct(*args):
        state.direct_calls += 1
        if state.primary_error is not None:
            raise state.primary_error
        return {"fixture": "direct passed"}

    def fake_application(base, model, report):
        state.application_calls += 1
        return "fixture-run", "fixture-hash"

    def fake_json(base, path):
        if path == "/api/runs/fixture-run":
            return {
                "run": {"status": "completed", "graph_hash": "fixture-hash", "graph_id": "g"},
                "snapshot": {"revision": 1},
            }
        if path == "/v1/models":
            return {"data": [{"id": "cg/g"}]}
        pytest.fail(f"Unexpected HTTP request: {path}")

    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected HTTP or inference effect")

    monkeypatch.setattr(module, "run", fake_run)
    monkeypatch.setattr(module.subprocess, "run", fake_subprocess)
    monkeypatch.setattr(module.socket, "socket", FakeSocket)
    monkeypatch.setattr(module, "direct_smoke", fake_direct)
    monkeypatch.setattr(module, "application_smoke", fake_application)
    monkeypatch.setattr(module, "json_request", fake_json)
    monkeypatch.setattr(module, "wait_ready", lambda base: None)
    monkeypatch.setattr(module, "performance_smoke", lambda *args: {})
    monkeypatch.setattr(module, "request", forbidden)
    monkeypatch.setattr(module.urllib.request, "build_opener", forbidden)
    return module, state


def assert_scoped_cleanup(state):
    down = [command for command in state.commands if "down" in command]
    assert down
    for command in down:
        assert command[command.index("-p") + 1] == PROJECT
        assert command[-3:] == ["down", "--timeout", "45"]
        assert "-v" not in command and "--volumes" not in command


def test_direct_success_retains_volume_and_checks_residue(smoke, capsys):
    module, state = smoke
    assert module.main() is None
    assert state.direct_calls == 1 and state.application_calls == 0
    assert_scoped_cleanup(state)
    report = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert report == {
        "residue_containers": [],
        "residue_networks": [],
        "retained_volume": VOLUME,
    }


def test_direct_cleanup_command_failure_preserves_exit_code(smoke):
    module, state = smoke
    state.down_error = 73
    with pytest.raises(module.CommandFailure) as failure:
        module.main()
    assert failure.value.exit_code == 73
    assert_scoped_cleanup(state)


@pytest.mark.parametrize("residue", ["container", "network"])
def test_direct_cleanup_residue_fails(smoke, residue):
    module, state = smoke
    state.residue = residue
    with pytest.raises(RuntimeError, match="Owned smoke container/network residue remains"):
        module.main()
    assert_scoped_cleanup(state)
    cleanup_index = next(i for i, command in enumerate(state.commands) if "down" in command)
    cleanup_commands = state.commands[cleanup_index + 1 :]
    assert any(command[1:3] == ["ps", "-aq"] for command in cleanup_commands)
    assert any(command[1:3] == ["network", "ls"] for command in cleanup_commands)
    for command in cleanup_commands:
        assert command[-1] == f"label=com.docker.compose.project={PROJECT}"


def test_primary_failure_wins_over_cleanup_failure(smoke, capsys):
    module, state = smoke
    state.primary_error = module.CommandFailure(["fixture-primary"], 29)
    state.down_error = 73
    with pytest.raises(module.CommandFailure) as failure:
        module.main()
    assert failure.value is state.primary_error and failure.value.exit_code == 29
    assert "Cleanup also failed" in capsys.readouterr().err
    assert_scoped_cleanup(state)


@pytest.mark.parametrize(
    "down_error,residue,primary_exit,expected_exit",
    [
        (73, None, None, 73),
        (None, "container", None, 1),
        (None, "network", None, 1),
        (73, None, 29, 29),
    ],
)
def test_cli_preserves_failure_exit(smoke, down_error, residue, primary_exit, expected_exit):
    module, state = smoke
    state.down_error = down_error
    state.residue = residue
    if primary_exit is not None:
        state.primary_error = module.CommandFailure(["fixture-primary"], primary_exit)
    # Execute the actual CLI guard with the fixture's isolated main function.
    guard = ast.parse(SMOKE_PATH.read_text(encoding="utf-8")).body[-1]
    cli = compile(ast.Module(body=[guard], type_ignores=[]), str(SMOKE_PATH), "exec")
    with pytest.raises(SystemExit) as failure:
        exec(cli, {**vars(module), "__name__": "__main__"})
    assert failure.value.code == expected_exit
    assert_scoped_cleanup(state)


@pytest.mark.parametrize("down_error", [None, 73])
def test_full_path_preserves_success_and_cleanup_failure(smoke, monkeypatch, down_error):
    module, state = smoke
    monkeypatch.setattr(sys, "argv", sys.argv[:-1])
    state.down_error = down_error
    # The first full-path down/up is a persistence check, not the final cleanup.
    original_run = module.run
    down_count = 0

    def run(command, **kwargs):
        nonlocal down_count
        if "down" in command:
            down_count += 1
            state.down_error = down_error if down_count == 2 else None
        return original_run(command, **kwargs)

    monkeypatch.setattr(module, "run", run)
    if down_error:
        with pytest.raises(module.CommandFailure) as failure:
            module.main()
        assert failure.value.exit_code == down_error
    else:
        assert module.main() is None
    assert state.application_calls == 1 and state.direct_calls == 0
    assert state.recreations == 2 and down_count == 2
    assert_scoped_cleanup(state)
