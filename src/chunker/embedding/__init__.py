"""Embedding package exports."""

from chunker.embedding.base import Embedder, l2_normalize, validate_embeddings
from chunker.embedding.mock import MockEmbedder

__all__ = [
    "Embedder",
    "MockEmbedder",
    "l2_normalize",
    "validate_embeddings",
]
