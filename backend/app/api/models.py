"""Published virtual models and external physical inventory; drafts stay hidden."""

from collections.abc import Callable

from fastapi import APIRouter, Depends

from app.contracts.api import ModelInfo, ModelsResponse
from app.contracts.interfaces import GraphRepository, OllamaAdapter


def create_models_router(
    graphs: GraphRepository, provider: OllamaAdapter, authorize: Callable
) -> APIRouter:
    router = APIRouter(prefix="/v1", dependencies=[Depends(authorize)])

    @router.get("/models", response_model=ModelsResponse)
    async def models() -> ModelsResponse:
        published = await graphs.list_published()
        physical = await provider.models()
        return ModelsResponse(
            data=[
                ModelInfo(id="cg/" + snapshot.graph_id, owned_by="cognitive-graph")
                for snapshot in published
            ]
            + [ModelInfo(id="ollama/" + name, owned_by="ollama") for name in physical]
        )

    return router
