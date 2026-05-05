"""Embedder abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


def validate_embeddings(matrix: np.ndarray, expected_count: int) -> np.ndarray:
    if expected_count == 0:
        if matrix.ndim == 2:
            return matrix.reshape(0, matrix.shape[1])
        return np.zeros((0, 0), dtype=np.float32)

    if matrix.ndim != 2:
        raise ValueError(f"Embeddings must be 2-D, got shape {matrix.shape}")
    if matrix.shape[0] != expected_count:
        raise ValueError(f"Expected {expected_count} embeddings, got {matrix.shape[0]}")
    if matrix.shape[1] == 0:
        raise ValueError("Embedding dimension must be > 0")
    if not np.isfinite(matrix).all():
        raise ValueError("Embeddings contain NaN or Inf values")
    return matrix.astype(np.float32, copy=False)


def l2_normalize(matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return matrix.astype(np.float32, copy=False)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return (matrix / norms).astype(np.float32)


class Embedder(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @property
    @abstractmethod
    def normalize(self) -> bool: ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> np.ndarray: ...

    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray: ...
