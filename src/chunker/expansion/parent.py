"""Parent expansion from retrieved children."""

from __future__ import annotations

from chunker.models import Chunk
from chunker.results import ExpandedContext, RetrievedChild


def expand_parents(
    retrieved: list[RetrievedChild],
    parents: dict[str, Chunk],
    documents: dict[str, object],
    *,
    missing_parent: str = "warn",
) -> list[ExpandedContext]:
    """
    Resolve each child to its parent. Does not dedupe yet.

    missing_parent: 'warn' skips with metadata warning; 'error' raises.
    """
    out: list[ExpandedContext] = []
    for hit in retrieved:
        if not hit.parent_id:
            # Direct strategy: child is its own context unit.
            doc = documents.get(hit.document_id)
            source = getattr(doc, "source", hit.document_id) if doc else hit.document_id
            out.append(
                ExpandedContext(
                    context_id=hit.child_id,
                    document_id=hit.document_id,
                    source=str(source),
                    text=hit.text,
                    derived_from=[hit.child_id],
                    metadata={"expansion": "identity"},
                )
            )
            continue

        parent = parents.get(hit.parent_id)
        if parent is None:
            msg = f"Missing parent {hit.parent_id} for child {hit.child_id}"
            if missing_parent == "error":
                raise ValueError(msg)
            out.append(
                ExpandedContext(
                    context_id=hit.child_id,
                    document_id=hit.document_id,
                    source=hit.document_id,
                    text=hit.text,
                    derived_from=[hit.child_id],
                    metadata={"expansion": "fallback_child", "warning": msg},
                )
            )
            continue

        doc = documents.get(parent.document_id)
        source = getattr(doc, "source", parent.document_id) if doc else parent.document_id
        out.append(
            ExpandedContext(
                context_id=parent.chunk_id,
                document_id=parent.document_id,
                source=str(source),
                text=parent.text,
                derived_from=[hit.child_id],
                start_char=parent.start_char,
                end_char=parent.end_char,
                metadata={"expansion": "parent"},
            )
        )
    return out
