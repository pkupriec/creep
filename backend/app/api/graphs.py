"""Graph CRUD/validation/publication routes with injected authorization.

create_graph_router(repository, validator, authorize) mounts /api/graphs and
applies the composition root's same authorization dependency to every route.
Import is create/save; export is the raw graph returned by GET. This module
never loads tokens or invents an authentication policy.
"""

import json
from collections.abc import Callable
from typing import TypeVar

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ValidationError

from app.contracts.api import (
    GraphListResponse,
    PublishGraphRequest,
    PublishGraphResponse,
    SaveGraphRequest,
    ValidationReport,
)
from app.contracts.config import MAX_REQUEST_BYTES
from app.contracts.errors import CGError, ErrorCode
from app.contracts.graph import Graph
from app.contracts.interfaces import GraphRepository, Validator, canonical_json

DTO = TypeVar("DTO", bound=BaseModel)


class _GraphRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def standard_errors(request: Request):
            try:
                return await handler(request)
            except CGError as exc:
                return JSONResponse(
                    exc.payload().model_dump(mode="json"), status_code=exc.status_code
                )
            except RequestValidationError:
                exc = CGError(ErrorCode.INVALID_PARAMETER, "Invalid request parameters.")
                return JSONResponse(exc.payload().model_dump(mode="json"), status_code=400)

        return standard_errors


async def _body(request: Request, model: type[DTO]) -> DTO:
    """Reject invalid JSON and Unicode before graph hashing or repository calls."""
    size = 0
    chunks = []
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_REQUEST_BYTES:
            raise CGError(ErrorCode.REQUEST_TOO_LARGE, "Request exceeds the size limit.")
        chunks.append(chunk)

    def unique_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate JSON key")
            value[key] = item
        return value

    try:
        payload = json.loads(b"".join(chunks), object_pairs_hook=unique_pairs)
        canonical_json(payload).encode("utf-8")
        return model.model_validate(payload)
    except (ValueError, ValidationError, RecursionError) as exc:
        raise CGError(ErrorCode.INVALID_PARAMETER, "Invalid graph request body.") from exc


def create_graph_router(
    repository: GraphRepository, validator: Validator, authorize: Callable[..., object]
) -> APIRouter:
    """Build an injectable router; authorization is mandatory at construction."""
    router = APIRouter(
        prefix="/api/graphs", dependencies=[Depends(authorize)], route_class=_GraphRoute
    )

    @router.get("", response_model=GraphListResponse)
    async def list_graphs() -> GraphListResponse:
        return GraphListResponse(graphs=list(await repository.list_graphs()))

    @router.post("", response_model=Graph, status_code=201)
    async def create_graph(request: Request) -> Graph:
        return await repository.create(await _body(request, Graph))

    @router.get("/{graph_id}", response_model=Graph)
    async def get_graph(graph_id: str) -> Graph:
        return await repository.get(graph_id)

    @router.put("/{graph_id}", response_model=Graph)
    async def save_graph(graph_id: str, request: Request) -> Graph:
        body = await _body(request, SaveGraphRequest)
        if body.graph.id != graph_id:
            raise CGError(ErrorCode.INVALID_PARAMETER, "Graph identifier must match the route.")
        return await repository.save(body.graph, body.expected_revision)

    @router.post("/{graph_id}/validate", response_model=ValidationReport)
    async def validate_graph(graph_id: str) -> ValidationReport:
        return validator.validate(await repository.get(graph_id))

    @router.post("/{graph_id}/publish", response_model=PublishGraphResponse)
    async def publish_graph(graph_id: str, request: Request) -> PublishGraphResponse:
        body = await _body(request, PublishGraphRequest)
        snapshot = await repository.publish(graph_id, body.expected_revision)
        return PublishGraphResponse(
            graph_id=snapshot.graph_id,
            published_revision=snapshot.revision,
            graph_hash=snapshot.graph_hash,
        )

    return router
