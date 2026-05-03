"""Core document and chunk models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class Document:
    """Normalized source document. Offsets refer to ``text``."""

    document_id: str
    source: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "source": self.source,
            "text": self.text,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Chunk:
    """Retrieval or context unit with provenance offsets."""

    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    parent_id: str | None = None
    level: int = 0
    start_token: int | None = None
    end_token: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "parent_id": self.parent_id,
            "text": self.text,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "start_token": self.start_token,
            "end_token": self.end_token,
            "chunk_index": self.chunk_index,
            "level": self.level,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chunk:
        return cls(
            chunk_id=data["chunk_id"],
            document_id=data["document_id"],
            chunk_index=int(data["chunk_index"]),
            text=data["text"],
            start_char=int(data["start_char"]),
            end_char=int(data["end_char"]),
            parent_id=data.get("parent_id"),
            level=int(data.get("level", 0)),
            start_token=data.get("start_token"),
            end_token=data.get("end_token"),
            metadata=dict(data.get("metadata") or {}),
        )


def make_chunk_id(document_id: str, kind: str, index: int) -> str:
    """Stable globally unique chunk id within an index."""
    return f"{document_id}_{kind}_{index:04d}"
