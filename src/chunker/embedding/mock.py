"""Deterministic mock embedder for tests (no model download)."""

from __future__ import annotations

import hashlib

import numpy as np

from chunker.embedding.base import Embedder, l2_normalize, validate_embeddings


class MockEmbedder(Embedder):
    def __init__(self, dimension: int = 32, seed: int = 0, *, normalize: bool = True) -> None:
        if dimension < 1:
            raise ValueError("dimension must be >= 1")
        self._dimension = dimension
        self._seed = seed
        self._normalize = normalize

    @property
    def model_name(self) -> str:
        return f"mock-embedder-d{self._dimension}-s{self._seed}"

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def normalize(self) -> bool:
        return self._normalize

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return self._embed(texts)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([text])[0]

    def _embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dimension), dtype=np.float32)
        rows = [self._vector_for(t) for t in texts]
        matrix = np.stack(rows, axis=0)
        if self._normalize:
            matrix = l2_normalize(matrix)
        return validate_embeddings(matrix, len(texts))

    def _vector_for(self, text: str) -> np.ndarray:
        digest = hashlib.sha256(f"{self._seed}:{text}".encode("utf-8")).digest()
        values = np.frombuffer(digest * ((self._dimension // 32) + 1), dtype=np.uint8)
        values = values[: self._dimension].astype(np.float32)
        return (values / 127.5) - 1.0
