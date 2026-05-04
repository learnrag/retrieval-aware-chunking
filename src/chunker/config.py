"""Experiment configuration defaults and validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ChunkStrategy = Literal["direct", "parent_child", "sentence_window"]
ExpansionStrategy = Literal["none", "parent", "sentence_window"]
Ordering = Literal["document", "score"]


@dataclass
class ChunkingConfig:
    strategy: ChunkStrategy = "parent_child"
    child_size_tokens: int = 256
    parent_size_tokens: int = 1024
    overlap_tokens: int = 32
    window_size: int = 2


@dataclass
class EmbeddingConfig:
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    normalize: bool = True


@dataclass
class RetrievalConfig:
    top_k: int = 5
    similarity: str = "cosine"


@dataclass
class ExpansionConfig:
    strategy: ExpansionStrategy = "parent"
    max_context_chars: int = 8192
    ordering: Ordering = "document"
    window_size: int = 2
    partial_context: bool = False


@dataclass
class StorageConfig:
    path: str = "./index"


@dataclass
class ProjectConfig:
    name: str = "retrieval-aware-chunker"
    version: str = "1.0"
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    expansion: ExpansionConfig = field(default_factory=ExpansionConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectConfig:
        chunking = ChunkingConfig(**(data.get("chunking") or {}))
        embedding = EmbeddingConfig(**(data.get("embedding") or {}))
        retrieval = RetrievalConfig(**(data.get("retrieval") or {}))
        expansion = ExpansionConfig(**(data.get("expansion") or {}))
        storage = StorageConfig(**(data.get("storage") or {}))
        return cls(
            name=data.get("name", "retrieval-aware-chunker"),
            version=data.get("version", "1.0"),
            chunking=chunking,
            embedding=embedding,
            retrieval=retrieval,
            expansion=expansion,
            storage=storage,
        )


def validate_top_k(top_k: int) -> int:
    if top_k < 1:
        raise ValueError("top_k must be >= 1")
    return top_k


def validate_budget(max_context_chars: int) -> int:
    if max_context_chars <= 0:
        raise ValueError("max_context_chars must be > 0")
    return max_context_chars
