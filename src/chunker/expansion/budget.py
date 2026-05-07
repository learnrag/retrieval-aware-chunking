"""Context budget enforcement without silent truncation of units."""

from __future__ import annotations

from chunker.results import ExpandedContext


def apply_budget(
    contexts: list[ExpandedContext],
    *,
    max_context_chars: int,
    partial_context: bool = False,
) -> tuple[list[ExpandedContext], dict]:
    """
    Stop before adding an item that would exceed the budget.

    If partial_context is True and the first item alone exceeds budget, include a
    truncated first item with an explicit metadata flag (only then).
    """
    if max_context_chars <= 0:
        raise ValueError("max_context_chars must be > 0")

    selected: list[ExpandedContext] = []
    used = 0
    truncated = False

    for ctx in contexts:
        size = len(ctx.text)
        if used + size <= max_context_chars:
            selected.append(ctx)
            used += size
            continue
        if not selected and partial_context and size > max_context_chars:
            selected.append(
                ExpandedContext(
                    context_id=ctx.context_id,
                    document_id=ctx.document_id,
                    source=ctx.source,
                    text=ctx.text[:max_context_chars],
                    derived_from=list(ctx.derived_from),
                    start_char=ctx.start_char,
                    end_char=ctx.end_char,
                    metadata={**ctx.metadata, "truncated": True},
                )
            )
            used = max_context_chars
            truncated = True
        break

    budget = {
        "unit": "chars",
        "max_context_chars": max_context_chars,
        "requested_chars": sum(len(c.text) for c in contexts),
        "returned_chars": used,
        "items_requested": len(contexts),
        "items_returned": len(selected),
        "truncated": truncated,
    }
    return selected, budget
