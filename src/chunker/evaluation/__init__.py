"""Benchmark evaluation runners."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chunker.config import ChunkStrategy, ExpansionStrategy
from chunker.embedding.base import Embedder
from chunker.evaluation.metrics import (
    GoldQuery,
    aggregate_metrics,
    context_recall,
    context_redundancy,
    context_size_chars,
    match_gold_children,
    mrr,
    precision_at_k,
    recall_at_k,
)
from chunker.pipeline import build_index, search
from chunker.storage.index import load_index


def load_benchmark(path: Path) -> list[GoldQuery]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    queries = data["queries"] if isinstance(data, dict) else data
    out: list[GoldQuery] = []
    for row in queries:
        out.append(
            GoldQuery(
                query_id=row["query_id"],
                query=row["query"],
                document_id=row["document_id"],
                gold_child_contains=list(row.get("gold_child_contains") or []),
                gold_context_contains=list(
                    row.get("gold_context_contains") or row.get("gold_child_contains") or []
                ),
                metadata=row.get("metadata"),
            )
        )
    return out


def evaluate_index(
    index_path: Path,
    benchmark: list[GoldQuery],
    embedder: Embedder,
    *,
    top_k: int = 5,
    expansion: ExpansionStrategy = "parent",
    window_size: int = 2,
) -> dict[str, Any]:
    index = load_index(index_path)
    children_texts = {c.chunk_id: c.text for c in index.children}
    rows: list[dict[str, float]] = []
    details: list[dict[str, Any]] = []

    for gq in benchmark:
        result = search(
            gq.query,
            index_path,
            embedder,
            top_k=top_k,
            expansion=expansion,
            window_size=window_size,
        )
        retrieved_ids = [r.child_id for r in result.results]
        scoped = {
            c.chunk_id: c.text
            for c in index.children
            if c.document_id == gq.document_id
        }
        relevant = match_gold_children(scoped, gq.gold_child_contains)
        expanded = [c.text for c in result.expanded_context]
        row = {
            "recall@k": recall_at_k(retrieved_ids, relevant, top_k),
            "precision@k": precision_at_k(retrieved_ids, relevant, top_k),
            "mrr": mrr(retrieved_ids, relevant),
            "context_recall": context_recall(expanded, gq.gold_context_contains),
            "context_size": float(context_size_chars(expanded)),
            "context_redundancy": context_redundancy(expanded),
        }
        rows.append(row)
        details.append(
            {
                "query_id": gq.query_id,
                "retrieved": retrieved_ids,
                "relevant": sorted(relevant),
                **row,
            }
        )

    return {"metrics": aggregate_metrics(rows), "details": details, "top_k": top_k, "expansion": expansion}


STRATEGY_MAP: dict[str, tuple[ChunkStrategy, ExpansionStrategy]] = {
    "direct": ("direct", "none"),
    "parent": ("parent_child", "parent"),
    "parent-child": ("parent_child", "parent"),
    "sentence-window": ("sentence_window", "sentence_window"),
    "sentence_window": ("sentence_window", "sentence_window"),
}


def compare_strategies(
    data_path: Path,
    benchmark_path: Path,
    work_dir: Path,
    embedder: Embedder,
    *,
    strategies: list[str],
    top_k: int = 5,
) -> dict[str, Any]:
    benchmark = load_benchmark(benchmark_path)
    report: dict[str, Any] = {"strategies": {}, "top_k": top_k}
    for name in strategies:
        key = name.strip().lower()
        if key not in STRATEGY_MAP:
            raise ValueError(f"Unknown strategy {name!r}; choose from {sorted(STRATEGY_MAP)}")
        chunk_strategy, expansion = STRATEGY_MAP[key]
        index_path = work_dir / f"index_{key.replace('-', '_')}"
        build_index(
            data_path,
            index_path,
            embedder,
            strategy=chunk_strategy,
            child_size_tokens=32,
            parent_size_tokens=128,
            overlap_tokens=4,
        )
        result = evaluate_index(
            index_path,
            benchmark,
            embedder,
            top_k=top_k,
            expansion=expansion,
            window_size=2,
        )
        report["strategies"][key] = result["metrics"]
    return report
