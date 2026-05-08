"""Retrieval and context evaluation metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class GoldQuery:
    query_id: str
    query: str
    document_id: str
    gold_child_contains: list[str]
    gold_context_contains: list[str]
    metadata: dict[str, Any] | None = None


def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top = set(retrieved_ids[:k])
    return 1.0 if top & relevant_ids else 0.0


def precision_at_k(retrieved_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = retrieved_ids[:k]
    if not top:
        return 0.0
    hits = sum(1 for r in top if r in relevant_ids)
    return hits / len(top)


def mrr(retrieved_ids: Sequence[str], relevant_ids: set[str]) -> float:
    for i, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / i
    return 0.0


def context_recall(expanded_texts: Iterable[str], gold_phrases: Sequence[str]) -> float:
    if not gold_phrases:
        return 0.0
    blob = "\n".join(expanded_texts)
    hits = sum(1 for p in gold_phrases if p in blob)
    return hits / len(gold_phrases)


def context_size_chars(expanded_texts: Iterable[str]) -> int:
    return sum(len(t) for t in expanded_texts)


def context_redundancy(expanded_texts: Sequence[str]) -> float:
    """Fraction of character mass that overlaps between consecutive contexts."""
    if len(expanded_texts) <= 1:
        return 0.0
    total = sum(len(t) for t in expanded_texts)
    if total == 0:
        return 0.0
    overlap = 0
    for a, b in zip(expanded_texts, expanded_texts[1:]):
        # Simple token-set overlap proxy
        ta = set(a.split())
        tb = set(b.split())
        if not ta or not tb:
            continue
        inter = ta & tb
        overlap += sum(len(w) for w in inter)
    return min(1.0, overlap / total)


def match_gold_children(children_texts: dict[str, str], phrases: Sequence[str]) -> set[str]:
    """Map gold phrases to child ids whose text contains the phrase."""
    relevant: set[str] = set()
    for cid, text in children_texts.items():
        for phrase in phrases:
            if phrase in text:
                relevant.add(cid)
                break
    return relevant


def aggregate_metrics(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {
            "recall@k": 0.0,
            "precision@k": 0.0,
            "mrr": 0.0,
            "context_recall": 0.0,
            "context_size": 0.0,
            "context_redundancy": 0.0,
            "n": 0.0,
        }
    keys = [
        "recall@k",
        "precision@k",
        "mrr",
        "context_recall",
        "context_size",
        "context_redundancy",
    ]
    out = {k: sum(r[k] for r in rows) / len(rows) for k in keys}
    out["n"] = float(len(rows))
    return out
