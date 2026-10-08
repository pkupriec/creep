"""Cross-platform development gates; missing implementation is a nonzero failure."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
COMPOSE_ENV = (
    "CG_API_TOKEN",
    "CG_DATA_DIR",
    "CG_SMOKE_MODEL",
    "CG_SMOKE_PROJECT",
    "DOCKER_CONTEXT",
    "DOCKER_HOST",
    "COMPOSE_PROJECT_NAME",
    "COMPOSE_FILE",
    "COMPOSE_PROFILES",
    "OLLAMA_BASE_URL",
    "CG_MAX_PARALLEL_LLM",
    "CG_MAX_ACTIVE_RUNS",
    "CG_MAX_QUEUED_RUNS",
    "CG_LLM_TIMEOUT_SECONDS",
    "CG_RUN_ACTIVE_TIMEOUT_SECONDS",
    "CG_TOOL_WAIT_TIMEOUT_SECONDS",
    "CG_MAX_NODE_EXECUTIONS",
    "CG_MAX_TOOL_ROUNDS",
    "CG_HISTORY_RETENTION_DAYS",
)


def execute(
    command: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    display: str | None = None,
) -> None:
    print("Run: " + (display or subprocess.list2cmdline(command)), flush=True)
    try:
        result = subprocess.run(command, cwd=cwd, env=env, check=False)
    except OSError:
        print("Required command could not start", file=sys.stderr)
        raise SystemExit(2) from None
    if result.returncode:
        raise SystemExit(result.returncode)


def require_executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        raise SystemExit(f"Required executable unavailable: {name}")
    return resolved


def uv(*arguments: str) -> None:
    execute([require_executable("uv"), "--system-certs", *arguments])


def backend(*arguments: str) -> None:
    uv("run", "--project", "backend", "--locked", *arguments)


def npm(*arguments: str) -> None:
    execute(
        [
            require_executable("npm.cmd" if os.name == "nt" else "npm"),
            "--prefix",
            str(FRONTEND),
            *arguments,
        ]
    )


def require_file(relative: str) -> None:
    if not (ROOT / relative).is_file():
        print(
            f"Gate unavailable: required implementation {relative} is absent",
            file=sys.stderr,
        )
        raise SystemExit(2)


def require_tests(relative: str, pattern: str) -> None:
    if not any((ROOT / relative).rglob(pattern)):
        print(f"Gate unavailable: no tests matching {relative}/{pattern}", file=sys.stderr)
        raise SystemExit(2)


def wsl_path(wsl: str, path: str) -> str:
    try:
        result = subprocess.run(
            [wsl, "--exec", "wslpath", "-a", path],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        print("WSL path conversion failed: command could not start", file=sys.stderr)
        raise SystemExit(2) from None
    converted = result.stdout.strip()
    if result.returncode or not converted.startswith("/") or "\n" in converted:
        print("WSL path conversion failed", file=sys.stderr)
        raise SystemExit(result.returncode or 2)
    return converted


def smoke_compose_windows(wsl: str, arguments: list[str]) -> None:
    converted_root = wsl_path(wsl, ROOT.as_posix())

    def compose_file(value: str) -> str:
        if not value:
            print("Compose file path must not be empty", file=sys.stderr)
            raise SystemExit(2)
        if PureWindowsPath(value).drive:
            return wsl_path(wsl, PureWindowsPath(value).as_posix())
        return value

    forwarded = []
    next_file = False
    for argument in arguments:
        if next_file:
            forwarded.append(compose_file(argument))
            next_file = False
        elif argument.startswith("--file="):
            forwarded.append("--file=" + compose_file(argument.partition("=")[2]))
        else:
            forwarded.append(argument)
            next_file = argument == "--file"
    child_env = dict(os.environ)
    if child_env.get("COMPOSE_FILE"):
        child_env["COMPOSE_FILE"] = ":".join(
            compose_file(value) for value in child_env["COMPOSE_FILE"].split(";")
        )
    # WSLENV exists only in this child. Values never enter shell text or logs.
    entries = [
        entry
        for entry in child_env.get("WSLENV", "").split(":")
        if entry and entry.split("/", 1)[0] not in COMPOSE_ENV
    ]
    entries.extend(name + "/u" for name in COMPOSE_ENV if name in child_env)
    child_env["WSLENV"] = ":".join(entries)
    execute(
        [wsl, "--cd", converted_root, "--exec", "bash", "scripts/smoke_compose.sh", *forwarded],
        env=child_env,
        display="WSL scripts/smoke_compose.sh (arguments forwarded)",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        choices=[
            "setup",
            "lint",
            "format",
            "test",
            "test-contract",
            "test-runtime",
            "test-graphs",
            "test-e2e",
            "smoke-hermes",
            "smoke-compose",
            "generate-contracts",
            "check-contracts",
            "build",
            "backend",
            "frontend",
        ],
    )
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help="Smoke helper options")
    args = parser.parse_args()
    target = args.target
    if args.arguments and target not in {"smoke-hermes", "smoke-compose"}:
        parser.error("Only smoke targets accept additional options")
    if target == "setup":
        uv("sync", "--project", "backend", "--locked", "--python", "3.11.15")
        npm("ci")
    elif target == "lint":
        backend(
            "ruff",
            "check",
            "--config",
            "backend/pyproject.toml",
            "backend/app",
            "backend/tests",
            "scripts",
        )
        backend(
            "ruff",
            "format",
            "--config",
            "backend/pyproject.toml",
            "--check",
            "backend/app",
            "backend/tests",
            "scripts",
        )
        backend("python", "scripts/export_contracts.py", "--check")
        npm("run", "typecheck")
    elif target == "format":
        backend(
            "ruff",
            "format",
            "--config",
            "backend/pyproject.toml",
            "backend/app",
            "backend/tests",
            "scripts",
        )
    elif target in {"generate-contracts", "check-contracts"}:
        backend(
            "python",
            "scripts/export_contracts.py",
            *(["--check"] if target == "check-contracts" else []),
        )
    elif target == "test":
        backend("pytest", "backend/tests", "-q")
        npm("test")
    elif target == "test-contract":
        backend("python", "scripts/export_contracts.py", "--check")
        test_paths = ["backend/tests/contracts"]
        for name in ("providers", "tools"):
            path = f"backend/tests/{name}"
            if (ROOT / path).is_dir():
                require_tests(path, "test_*.py")
                test_paths.append(path)
        backend("pytest", *test_paths, "-q")
        npm("run", "test:contract")
    elif target in {"test-runtime", "test-graphs"}:
        paths = (
            ["backend/tests/runtime", "backend/tests/storage"]
            if target == "test-runtime"
            else ["backend/tests/graphs"]
        )
        for path in paths:
            require_tests(path, "test_*.py")
        backend("pytest", *paths, "-q")
    elif target == "test-e2e":
        require_file("frontend/playwright.config.ts")
        require_file("frontend/src/main.tsx")
        require_tests("frontend/e2e", "*.spec.ts")
        npm("run", "test:e2e")
    elif target == "smoke-hermes":
        require_file("scripts/smoke_hermes.py")
        backend("python", "scripts/smoke_hermes.py", *args.arguments)
    elif target == "smoke-compose":
        require_file("scripts/smoke_compose.sh")
        require_file("compose.yaml")
        if os.name == "nt":
            smoke_compose_windows(require_executable("wsl.exe"), args.arguments)
        else:
            execute([require_executable("bash"), "scripts/smoke_compose.sh", *args.arguments])
    elif target == "build":
        require_file("frontend/src/main.tsx")
        npm("run", "build")
    elif target == "backend":
        # Explicit one-process launch: no interprocess scheduler exists.
        uv(
            "run",
            "--project",
            "backend",
            "--locked",
            "uvicorn",
            "app.main:app",
            "--app-dir",
            "backend",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--workers",
            "1",
        )
    elif target == "frontend":
        require_file("frontend/src/main.tsx")
        npm("run", "dev")


if __name__ == "__main__":
    main()
