"""Build-index and search orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from chunker.chunking import build_chunks
from chunker.config import (
    ChunkStrategy,
    ExpansionStrategy,
    ProjectConfig,
    validate_budget,
    validate_top_k,
)
from chunker.embedding.base import Embedder
from chunker.expansion import (
    apply_budget,
    dedupe_contexts,
    expand_parents,
    expand_windows,
    order_contexts,
)
from chunker.ingest import ingest_directory, ingest_file
from chunker.models import SCHEMA_VERSION, Chunk, Document
from chunker.results import RetrievedChild, RetrievalResult
from chunker.retrieval.exact_search import top_k_search
from chunker.storage.index import LoadedIndex, load_index, save_index


def _load_documents(data_path: Path) -> list[Document]:
    data_path = Path(data_path)
    if data_path.is_file():
        return [ingest_file(data_path)]
    return ingest_directory(data_path)


def build_index(
    data_path: str | Path,
    index_path: str | Path,
    embedder: Embedder,
    *,
    strategy: ChunkStrategy = "parent_child",
    child_size_tokens: int = 256,
    parent_size_tokens: int = 1024,
    overlap_tokens: int = 32,
    config: ProjectConfig | None = None,
) -> dict[str, Any]:
    documents = _load_documents(Path(data_path))
    all_parents: list[Chunk] = []
    all_children: list[Chunk] = []

    for doc in documents:
        parents, children = build_chunks(
            doc,
            strategy,
            child_size_tokens=child_size_tokens,
            parent_size_tokens=parent_size_tokens,
            overlap_tokens=overlap_tokens,
        )
        if strategy == "parent_child":
            all_parents.extend(parents)
        all_children.extend(children)

    embeddings = embedder.embed_documents([c.text for c in all_children])
    cfg = config or ProjectConfig()
    cfg.chunking.strategy = strategy
    cfg.chunking.child_size_tokens = child_size_tokens
    cfg.chunking.parent_size_tokens = parent_size_tokens
    cfg.chunking.overlap_tokens = overlap_tokens
    cfg.embedding.model = embedder.model_name
    cfg.embedding.normalize = embedder.normalize
    cfg.storage.path = str(index_path)

    model_meta = {
        "model": embedder.model_name,
        "dimension": embedder.dimension,
        "normalize": embedder.normalize,
        "schema_version": SCHEMA_VERSION,
    }
    save_index(
        Path(index_path),
        children=all_children,
        parents=all_parents,
        documents=documents,
        embeddings=embeddings,
        model_meta=model_meta,
        config=cfg.to_dict(),
    )
    return {
        "documents": len(documents),
        "children": len(all_children),
        "parents": len(all_parents),
        "dimension": embedder.dimension,
        "index_path": str(index_path),
    }


def _expand(
    strategy: ExpansionStrategy,
    retrieved: list[RetrievedChild],
    index: LoadedIndex,
    *,
    window_size: int,
) -> list:
    if strategy == "none":
        from chunker.results import ExpandedContext

        return [
            ExpandedContext(
                context_id=r.child_id,
                document_id=r.document_id,
                source=index.documents.get(r.document_id).source
                if r.document_id in index.documents
                else r.document_id,
                text=r.text,
                derived_from=[r.child_id],
                metadata={"expansion": "none"},
            )
            for r in retrieved
        ]
    if strategy == "parent":
        return expand_parents(retrieved, index.parents, index.documents)
    if strategy == "sentence_window":
        return expand_windows(
            retrieved,
            index.children,
            index.documents,
            window_size=window_size,
        )
    raise ValueError(f"Unknown expansion strategy: {strategy}")


def search(
    query: str,
    index_path: str | Path,
    embedder: Embedder,
    *,
    top_k: int | None = None,
    expansion: ExpansionStrategy | None = None,
    max_context_chars: int | None = None,
    window_size: int | None = None,
    ordering: str | None = None,
    explain: bool = False,
) -> RetrievalResult:
    expected = {
        "model": embedder.model_name,
        "dimension": embedder.dimension,
        "normalize": embedder.normalize,
    }
    index = load_index(Path(index_path), expected_model=expected)
    cfg = ProjectConfig.from_dict(index.config)

    k = validate_top_k(top_k if top_k is not None else cfg.retrieval.top_k)
    exp = expansion if expansion is not None else cfg.expansion.strategy
    budget_limit = validate_budget(
        max_context_chars if max_context_chars is not None else cfg.expansion.max_context_chars
    )
    win = window_size if window_size is not None else cfg.expansion.window_size
    order = ordering if ordering is not None else cfg.expansion.ordering

    if not query.strip():
        return RetrievalResult(
            query=query,
            results=[],
            expanded_context=[],
            budget={
                "unit": "chars",
                "max_context_chars": budget_limit,
                "requested_chars": 0,
                "returned_chars": 0,
                "items_requested": 0,
                "items_returned": 0,
                "truncated": False,
            },
            explain={"warning": "empty query"} if explain else {},
        )

    qvec = embedder.embed_query(query)
    hits = top_k_search(
        qvec,
        index.embeddings,
        index.children,
        top_k=k,
        normalized=embedder.normalize,
    )
    retrieved = [
        RetrievedChild(
            child_id=chunk.chunk_id,
            score=score,
            text=chunk.text,
            document_id=chunk.document_id,
            parent_id=chunk.parent_id,
            metadata=dict(chunk.metadata),
        )
        for chunk, score in hits
    ]

    contexts = _expand(exp, retrieved, index, window_size=win)
    contexts = dedupe_contexts(contexts)
    contexts = order_contexts(contexts, retrieved, ordering=order)  # type: ignore[arg-type]
    contexts, budget = apply_budget(contexts, max_context_chars=budget_limit)

    explain_payload: dict[str, Any] = {}
    if explain:
        explain_payload = {
            "stages": [
                "query_embed",
                "exact_search",
                f"expand:{exp}",
                "dedupe",
                f"order:{order}",
                "budget",
            ],
            "top_k": k,
            "child_count": len(index.children),
            "model": embedder.model_name,
            "scores": [{"child_id": r.child_id, "score": r.score} for r in retrieved],
        }

    return RetrievalResult(
        query=query,
        results=retrieved,
        expanded_context=contexts,
        budget=budget,
        explain=explain_payload,
    )


def inspect_chunk(index_path: str | Path, chunk_id: str) -> dict[str, Any]:
    index = load_index(Path(index_path))
    child = next((c for c in index.children if c.chunk_id == chunk_id), None)
    parent = None
    if child and child.parent_id:
        parent = index.parents.get(child.parent_id)
    if child is None and chunk_id in index.parents:
        parent = index.parents[chunk_id]
    if child is None and parent is None:
        raise KeyError(f"Chunk not found: {chunk_id}")
    return {
        "child": child.to_dict() if child else None,
        "parent": parent.to_dict() if parent else None,
        "document": index.documents.get(child.document_id).to_dict()
        if child and child.document_id in index.documents
        else (
            index.documents.get(parent.document_id).to_dict()
            if parent and parent.document_id in index.documents
            else None
        ),
    }
