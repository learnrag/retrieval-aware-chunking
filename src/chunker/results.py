"""Retrieval and expansion result contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RetrievedChild:
    child_id: str
    score: float
    text: str
    document_id: str
    parent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "child_id": self.child_id,
            "score": self.score,
            "text": self.text,
            "document_id": self.document_id,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ExpandedContext:
    context_id: str
    document_id: str
    source: str
    text: str
    derived_from: list[str]
    start_char: int | None = None
    end_char: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "document_id": self.document_id,
            "source": self.source,
            "text": self.text,
            "derived_from": list(self.derived_from),
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata,
        }


@dataclass
class RetrievalResult:
    query: str
    results: list[RetrievedChild]
    expanded_context: list[ExpandedContext]
    budget: dict[str, Any] = field(default_factory=dict)
    explain: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "expanded_context": [c.to_dict() for c in self.expanded_context],
            "budget": self.budget,
            "explain": self.explain,
        }
