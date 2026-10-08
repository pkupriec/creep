"""One-process configuration; environment token is never serialized or logged."""

import hashlib
import os
from collections.abc import Mapping
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator

from .graph import Contract, PositiveInt

# Transport boundaries, not inference-cache or scheduler-concurrency settings.
MAX_REQUEST_BYTES = 2 * 1024 * 1024
MAX_GRAPH_BYTES = 512 * 1024
MAX_TOOL_RESULT_BYTES = 1024 * 1024


class Settings(Contract):
    ollama_base_url: str = "http://host.docker.internal:11434/v1"
    data_dir: str = "/data"
    api_token: SecretStr | None = Field(default=None, exclude=True, repr=False)
    max_parallel_llm: PositiveInt = 2
    max_active_runs: PositiveInt = 4
    max_queued_runs: PositiveInt = 20
    llm_timeout_seconds: PositiveInt = 300
    run_active_timeout_seconds: PositiveInt = 1800
    tool_wait_timeout_seconds: PositiveInt = 1800
    max_node_executions: PositiveInt = 100
    max_tool_rounds: PositiveInt = 20
    history_retention_days: PositiveInt = 30

    @field_validator("ollama_base_url")
    @classmethod
    def endpoint(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path.rstrip("/") != "/v1"
        ):
            raise ValueError("OLLAMA_BASE_URL must be an HTTP(S) /v1 URL without credentials")
        try:
            _ = parsed.port
        except ValueError:
            raise ValueError("OLLAMA_BASE_URL has an invalid port") from None
        return value.rstrip("/")

    @field_validator("data_dir")
    @classmethod
    def nonempty_data_dir(cls, value: str) -> str:
        if not value.strip() or "\0" in value:
            raise ValueError("CG_DATA_DIR must be nonempty")
        return value

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if environ is None else environ
        if source.get("WEB_CONCURRENCY", "1") != "1":
            raise ValueError("Only one backend worker is supported")
        values: dict = {}
        for field in cls.model_fields:
            env_name = "OLLAMA_BASE_URL" if field == "ollama_base_url" else "CG_" + field.upper()
            raw = source.get(env_name)
            if raw is None:
                continue
            if field == "api_token":
                values[field] = SecretStr(raw) if raw else None
            elif field in {"ollama_base_url", "data_dir"}:
                values[field] = raw
            else:
                try:
                    values[field] = int(raw)
                except ValueError:
                    raise ValueError(f"{env_name} must be a positive integer") from None
        return cls.model_validate(values)

    def caller_namespace(self) -> str:
        if self.api_token is None:
            return "anonymous"
        token = self.api_token.get_secret_value()
        return hashlib.sha256(("cognitive-graph-caller-v1\0" + token).encode()).hexdigest()
