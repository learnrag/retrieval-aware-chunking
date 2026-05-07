"""Sentence-window expansion and overlap merging."""

from __future__ import annotations

from chunker.chunking.sentence_window import expand_window_from_document
from chunker.models import Chunk, Document
from chunker.results import ExpandedContext, RetrievedChild


def expand_windows(
    retrieved: list[RetrievedChild],
    children: list[Chunk],
    documents: dict[str, Document],
    *,
    window_size: int = 2,
) -> list[ExpandedContext]:
    """Expand each retrieved sentence, then merge overlapping windows per document."""
    by_doc: dict[str, list[Chunk]] = {}
    for c in children:
        by_doc.setdefault(c.document_id, []).append(c)
    for doc_id in by_doc:
        by_doc[doc_id] = sorted(by_doc[doc_id], key=lambda c: c.chunk_index)

    # Collect raw windows
    raw: list[ExpandedContext] = []
    for hit in retrieved:
        sentences = by_doc.get(hit.document_id, [])
        if not sentences:
            continue
        index_map = {c.chunk_id: i for i, c in enumerate(sentences)}
        if hit.child_id not in index_map:
            continue
        center = index_map[hit.child_id]
        doc = documents.get(hit.document_id)
        if doc is None:
            continue
        start_i, end_i, text, start_char, end_char = expand_window_from_document(
            doc.text, sentences, center, window_size
        )
        raw.append(
            ExpandedContext(
                context_id=f"{hit.document_id}_window_{start_i:04d}_{end_i:04d}",
                document_id=hit.document_id,
                source=doc.source,
                text=text,
                derived_from=[hit.child_id],
                start_char=start_char,
                end_char=end_char,
                metadata={
                    "expansion": "sentence_window",
                    "sentence_start": start_i,
                    "sentence_end": end_i,
                },
            )
        )

    return merge_overlapping_windows(raw)


def merge_overlapping_windows(windows: list[ExpandedContext]) -> list[ExpandedContext]:
    """Merge overlapping/adjacent windows within the same document by char span."""
    if not windows:
        return []

    by_doc: dict[str, list[ExpandedContext]] = {}
    for w in windows:
        by_doc.setdefault(w.document_id, []).append(w)

    merged: list[ExpandedContext] = []
    for doc_id, group in by_doc.items():
        ordered = sorted(
            group,
            key=lambda w: (w.start_char if w.start_char is not None else 0, w.context_id),
        )
        cur = ordered[0]
        for nxt in ordered[1:]:
            cur_end = cur.end_char if cur.end_char is not None else -1
            nxt_start = nxt.start_char if nxt.start_char is not None else 0
            if nxt_start <= cur_end:
                # Overlap: extend
                new_end = max(cur_end, nxt.end_char or cur_end)
                # Prefer longer text from char span if both share source offsets
                if cur.start_char is not None and new_end is not None:
                    # Reconstruct by concatenation of unique derived_from and span metadata
                    text = _merge_text(cur, nxt)
                else:
                    text = cur.text if len(cur.text) >= len(nxt.text) else nxt.text
                cur = ExpandedContext(
                    context_id=f"{doc_id}_window_{cur.metadata.get('sentence_start', 0):04d}_"
                    f"{max(cur.metadata.get('sentence_end', 0), nxt.metadata.get('sentence_end', 0)):04d}",
                    document_id=doc_id,
                    source=cur.source,
                    text=text,
                    derived_from=list(dict.fromkeys([*cur.derived_from, *nxt.derived_from])),
                    start_char=cur.start_char,
                    end_char=new_end,
                    metadata={
                        "expansion": "sentence_window",
                        "sentence_start": min(
                            cur.metadata.get("sentence_start", 0),
                            nxt.metadata.get("sentence_start", 0),
                        ),
                        "sentence_end": max(
                            cur.metadata.get("sentence_end", 0),
                            nxt.metadata.get("sentence_end", 0),
                        ),
                        "merged": True,
                    },
                )
            else:
                merged.append(cur)
                cur = nxt
        merged.append(cur)
    return merged


def _merge_text(a: ExpandedContext, b: ExpandedContext) -> str:
    if a.start_char is None or a.end_char is None or b.start_char is None or b.end_char is None:
        return a.text if len(a.text) >= len(b.text) else b.text
    if a.start_char <= b.start_char and a.end_char >= b.end_char:
        return a.text
    if b.start_char <= a.start_char and b.end_char >= a.end_char:
        return b.text
    # Partial overlap: stitch by relative offsets into combined span
    start = min(a.start_char, b.start_char)
    end = max(a.end_char, b.end_char)
    buf = [" "] * (end - start)
    for ctx in (a, b):
        offset = ctx.start_char - start
        for i, ch in enumerate(ctx.text):
            pos = offset + i
            if 0 <= pos < len(buf):
                buf[pos] = ch
    return "".join(buf).rstrip()
