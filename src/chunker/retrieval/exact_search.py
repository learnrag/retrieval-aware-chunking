"""Exact cosine similarity search over child embeddings."""

from __future__ import annotations

import numpy as np

from chunker.embedding.base import l2_normalize
from chunker.models import Chunk


def cosine_scores(query: np.ndarray, matrix: np.ndarray, *, normalized: bool) -> np.ndarray:
    """Return similarity scores for one query against all rows."""
    if matrix.size == 0:
        return np.zeros((0,), dtype=np.float32)
    q = np.asarray(query, dtype=np.float32).reshape(-1)
    if q.shape[0] != matrix.shape[1]:
        raise ValueError(
            f"Query dim {q.shape[0]} does not match index dim {matrix.shape[1]}"
        )
    if normalized:
        return matrix @ q
    qn = l2_normalize(q.reshape(1, -1))[0]
    mn = l2_normalize(matrix)
    return mn @ qn


def top_k_search(
    query: np.ndarray,
    matrix: np.ndarray,
    children: list[Chunk],
    *,
    top_k: int,
    normalized: bool = True,
) -> list[tuple[Chunk, float]]:
    """Exact top-K with deterministic chunk_id tie-break."""
    if top_k < 1:
        raise ValueError("top_k must be >= 1")
    if len(children) != matrix.shape[0]:
        raise ValueError("children count must match embedding rows")
    if not children:
        return []

    scores = cosine_scores(query, matrix, normalized=normalized)
    # Sort by (-score, chunk_id)
    order = sorted(
        range(len(children)),
        key=lambda i: (-float(scores[i]), children[i].chunk_id),
    )
    k = min(top_k, len(order))
    return [(children[i], float(scores[i])) for i in order[:k]]
