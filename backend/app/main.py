"""Single-worker composition root, injectable for actual HTTP integration tests.

Lifespan initializes SQLite, recovers checkpoints and starts retention cleanup.
Shutdown joins runtime work before closing its provider and repository. External
Ollama availability is separate from storage/recovery readiness.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.chat import create_chat_router
from app.api.graphs import create_graph_router
from app.api.models import create_models_router
from app.api.runs import create_runs_router
from app.api.security import BodyLimitMiddleware, authorization
from app.contracts.api import HealthResponse
from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import (
    AdmissionController,
    Clock,
    EventBus,
    GraphRepository,
    GraphRuntime,
    OllamaAdapter,
    RunRepository,
    ToolBridge,
    Validator,
)
from app.graphs.repository import FileGraphRepository
from app.graphs.validator import GraphValidator
from app.providers.ollama import HttpOllamaAdapter
from app.runtime.admission import BoundedAdmissionController
from app.runtime.clock import SystemClock
from app.runtime.engine import AsyncGraphRuntime
from app.storage.events import DurableEventBus
from app.storage.repository import SQLiteRunRepository
from app.tools.bridge import DurableToolBridge


def create_app(
    settings: Settings | None = None,
    *,
    provider: OllamaAdapter | None = None,
    repository: RunRepository | None = None,
    graphs: GraphRepository | None = None,
    validator: Validator | None = None,
    clock: Clock | None = None,
    admission: AdmissionController | None = None,
    runtime: GraphRuntime | None = None,
    bridge: ToolBridge | None = None,
    events: EventBus | None = None,
) -> FastAPI:
    """Construct shared services without opening SQLite until lifespan starts.

    Injected components participate in this app's lifecycle. HttpOllamaAdapter
    retains its documented ownership of an injected HTTP client's closure.
    """
    settings = settings or Settings.from_env()
    validator = validator or GraphValidator()
    clock = clock or SystemClock()
    repository = repository or SQLiteRunRepository(Path(settings.data_dir) / "runtime.sqlite")
    graphs = graphs or FileGraphRepository(Path(settings.data_dir), validator)
    events = events or DurableEventBus(repository)
    admission = admission or BoundedAdmissionController(
        settings.max_active_runs, settings.max_queued_runs
    )
    provider = provider or HttpOllamaAdapter(
        settings, limiter=asyncio.Semaphore(settings.max_parallel_llm)
    )
    bridge = bridge or DurableToolBridge(settings, repository, events, clock)
    runtime = runtime or AsyncGraphRuntime(
        settings, repository, validator, provider, bridge, events, admission, clock
    )

    async def retention():
        while True:
            await asyncio.sleep(3600)
            try:
                await repository.cleanup_history(
                    clock.now() - timedelta(days=settings.history_retention_days)
                )
            except CGError:
                app.state.storage_ready = False
            else:
                app.state.storage_ready = True

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.storage_ready = False
        cleanup = None
        try:
            await repository.initialize()
            await runtime.recover()
            application.state.storage_ready = True
            cleanup = asyncio.create_task(retention(), name="cg-history-retention")
            yield
        finally:
            application.state.storage_ready = False
            if cleanup is not None:
                cleanup.cancel()
                await asyncio.gather(cleanup, return_exceptions=True)
            try:
                await runtime.shutdown()
            finally:
                try:
                    await provider.close()
                finally:
                    await repository.close()

    app = FastAPI(title="Cognitive Graph", version="0.1.0", lifespan=lifespan)
    app.state.storage_ready = False
    for name, component in {
        "settings": settings,
        "graphs": graphs,
        "validator": validator,
        "repository": repository,
        "events": events,
        "admission": admission,
        "provider": provider,
        "bridge": bridge,
        "runtime": runtime,
        "clock": clock,
    }.items():
        setattr(app.state, name, component)
    app.add_middleware(BodyLimitMiddleware)

    @app.exception_handler(CGError)
    async def error_handler(_: Request, error: CGError):
        return JSONResponse(error.payload().model_dump(mode="json"), status_code=error.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, __: RequestValidationError):
        return await error_handler(
            _, CGError(ErrorCode.INVALID_PARAMETER, "Invalid request parameters.")
        )

    @app.exception_handler(Exception)
    async def unexpected_handler(_: Request, __: Exception):
        return await error_handler(
            _, CGError(ErrorCode.STORAGE_ERROR, "Internal service operation failed.")
        )

    @app.get("/health/live", response_model=HealthResponse)
    async def live():
        return HealthResponse(
            status="ok", storage_ready=app.state.storage_ready, ollama_available=False
        )

    @app.get("/health/ready", response_model=HealthResponse)
    async def ready():
        healthy = app.state.storage_ready
        if healthy:
            try:
                await repository.list_runs(
                    settings.caller_namespace(), graph_id=None, status=None, limit=1, offset=0
                )
            except CGError:
                healthy = False
        try:
            async with asyncio.timeout(min(5, settings.llm_timeout_seconds)):
                upstream = await provider.health()
        except TimeoutError:
            upstream = False
        body = HealthResponse(
            status="ok" if healthy else "unavailable",
            storage_ready=healthy,
            ollama_available=upstream,
        )
        return JSONResponse(body.model_dump(), status_code=200 if healthy else 503)

    authorize = authorization(settings)
    app.include_router(create_graph_router(graphs, validator, authorize))
    app.include_router(create_models_router(graphs, provider, authorize))
    app.include_router(
        create_runs_router(
            settings, graphs, validator, repository, runtime, bridge, events, clock, authorize
        )
    )
    app.include_router(
        create_chat_router(
            settings, graphs, validator, provider, runtime, bridge, admission, authorize
        )
    )
    return app


app = create_app()
