"""Deduplicate and order expanded contexts."""

from __future__ import annotations

from chunker.config import Ordering
from chunker.results import ExpandedContext, RetrievedChild


def dedupe_contexts(contexts: list[ExpandedContext]) -> list[ExpandedContext]:
    """Merge contexts that share the same context_id; union derived_from."""
    by_id: dict[str, ExpandedContext] = {}
    for ctx in contexts:
        existing = by_id.get(ctx.context_id)
        if existing is None:
            by_id[ctx.context_id] = ctx
            continue
        by_id[ctx.context_id] = ExpandedContext(
            context_id=ctx.context_id,
            document_id=ctx.document_id,
            source=ctx.source,
            text=ctx.text if len(ctx.text) >= len(existing.text) else existing.text,
            derived_from=list(dict.fromkeys([*existing.derived_from, *ctx.derived_from])),
            start_char=ctx.start_char if ctx.start_char is not None else existing.start_char,
            end_char=ctx.end_char if ctx.end_char is not None else existing.end_char,
            metadata={**existing.metadata, **ctx.metadata, "deduped": True},
        )
    return list(by_id.values())


def order_contexts(
    contexts: list[ExpandedContext],
    retrieved: list[RetrievedChild],
    *,
    ordering: Ordering = "document",
) -> list[ExpandedContext]:
    if ordering == "document":
        return sorted(
            contexts,
            key=lambda c: (
                c.document_id,
                c.start_char if c.start_char is not None else 10**12,
                c.context_id,
            ),
        )

    # score order: best child score among derived_from
    score_map = {r.child_id: r.score for r in retrieved}

    def best_score(ctx: ExpandedContext) -> float:
        scores = [score_map[d] for d in ctx.derived_from if d in score_map]
        return max(scores) if scores else float("-inf")

    return sorted(contexts, key=lambda c: (-best_score(c), c.context_id))
