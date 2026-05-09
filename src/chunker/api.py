"""FastAPI HTTP API for retrieval-aware chunking."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from chunker.embedding.mock import MockEmbedder
from chunker.pipeline import build_index, inspect_chunk, search

ChunkStrategy = Literal["direct", "parent_child", "sentence_window"]
ExpansionStrategy = Literal["none", "parent", "sentence_window"]

app = FastAPI(
    title="retrieval-aware-chunker",
    description="Child retrieval with parent/sentence-window expansion",
    version="0.1.0",
)

_default_embedder = None


def _get_default_embedder(model_name: str):
    global _default_embedder
    if _default_embedder is not None and _default_embedder.model_name == model_name:
        return _default_embedder
    from chunker.embedding.sentence_transformers import SentenceTransformerEmbedder

    _default_embedder = SentenceTransformerEmbedder(model_name=model_name)
    return _default_embedder


def _resolve_embedder(mock: bool, model: str, mock_dim: int = 32):
    if mock:
        return MockEmbedder(dimension=mock_dim)
    return _get_default_embedder(model)


class HealthResponse(BaseModel):
    status: str


class BuildRequest(BaseModel):
    data_path: str
    index_path: str = "./index"
    strategy: ChunkStrategy = "parent_child"
    child_size_tokens: int = Field(256, ge=1)
    parent_size_tokens: int = Field(1024, ge=1)
    overlap_tokens: int = Field(32, ge=0)
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    mock: bool = False


class SearchRequest(BaseModel):
    query: str
    index_path: str = "./index"
    top_k: int = Field(5, ge=1)
    expansion: ExpansionStrategy | None = None
    max_context_chars: int | None = Field(None, gt=0)
    window_size: int = Field(2, ge=0)
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    mock: bool = False
    explain: bool = False


class InspectRequest(BaseModel):
    chunk_id: str
    index_path: str = "./index"


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/build")
def build_endpoint(req: BuildRequest) -> dict[str, Any]:
    try:
        embedder = _resolve_embedder(req.mock, req.model)
        return build_index(
            req.data_path,
            req.index_path,
            embedder,
            strategy=req.strategy,
            child_size_tokens=req.child_size_tokens,
            parent_size_tokens=req.parent_size_tokens,
            overlap_tokens=req.overlap_tokens,
        )
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/search")
def search_endpoint(req: SearchRequest) -> dict[str, Any]:
    try:
        embedder = _resolve_embedder(req.mock, req.model)
        result = search(
            req.query,
            req.index_path,
            embedder,
            top_k=req.top_k,
            expansion=req.expansion,
            max_context_chars=req.max_context_chars,
            window_size=req.window_size,
            explain=req.explain,
        )
        return result.to_dict()
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/inspect")
def inspect_endpoint(req: InspectRequest) -> dict[str, Any]:
    try:
        return inspect_chunk(Path(req.index_path), req.chunk_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def run() -> None:
    import uvicorn

    uvicorn.run("chunker.api:app", host="0.0.0.0", port=8000, reload=False)
