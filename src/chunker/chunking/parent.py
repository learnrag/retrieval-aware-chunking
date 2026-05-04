"""Parent-child hierarchical chunking."""

from __future__ import annotations

import re

from chunker.chunking.child import split_text_by_tokens
from chunker.chunking.tokens import tokenize_whitespace
from chunker.models import Chunk, Document, make_chunk_id

_HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+.+$")


def _section_ranges(text: str) -> list[tuple[int, int]]:
    """Split on Markdown ATX headings; fallback is whole document."""
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [(0, len(text))] if text else []

    ranges: list[tuple[int, int]] = []
    # Preface before first heading
    if matches[0].start() > 0:
        preface = text[: matches[0].start()]
        if preface.strip():
            ranges.append((0, matches[0].start()))

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if text[start:end].strip():
            ranges.append((start, end))
    return ranges


def _pack_parent_ranges(
    text: str,
    section_ranges: list[tuple[int, int]],
    parent_size_tokens: int,
) -> list[tuple[int, int]]:
    """Merge or split sections to approximate parent_size_tokens."""
    if parent_size_tokens < 1:
        raise ValueError("parent_size_tokens must be >= 1")

    packed: list[tuple[int, int]] = []
    for start, end in section_ranges:
        section = text[start:end]
        tokens = tokenize_whitespace(section)
        if len(tokens) <= parent_size_tokens:
            packed.append((start, end))
            continue
        # Oversized section: split by token windows without overlap.
        pieces = split_text_by_tokens(
            section, size_tokens=parent_size_tokens, overlap_tokens=0
        )
        for local_start, local_end, *_ in pieces:
            packed.append((start + local_start, start + local_end))
    return packed


def chunk_parent_child(
    document: Document,
    *,
    child_size_tokens: int = 256,
    parent_size_tokens: int = 1024,
    overlap_tokens: int = 32,
) -> tuple[list[Chunk], list[Chunk]]:
    """
    Build parent context units and child retrieval units.

    Returns (parents, children). Only children are embedded for MVP.
    """
    section_ranges = _section_ranges(document.text)
    if not section_ranges and document.text.strip():
        section_ranges = [(0, len(document.text))]

    parent_ranges = _pack_parent_ranges(
        document.text, section_ranges, parent_size_tokens
    )

    parents: list[Chunk] = []
    children: list[Chunk] = []
    child_index = 0

    for p_idx, (p_start, p_end) in enumerate(parent_ranges):
        parent_text = document.text[p_start:p_end]
        parent_id = make_chunk_id(document.document_id, "parent", p_idx)
        parents.append(
            Chunk(
                chunk_id=parent_id,
                document_id=document.document_id,
                chunk_index=p_idx,
                text=parent_text,
                start_char=p_start,
                end_char=p_end,
                parent_id=None,
                level=0,
                metadata={"kind": "parent", "strategy": "parent_child"},
            )
        )

        pieces = split_text_by_tokens(
            parent_text,
            size_tokens=child_size_tokens,
            overlap_tokens=overlap_tokens,
        )
        if not pieces and parent_text.strip():
            pieces = [(0, len(parent_text), 0, 0, parent_text)]

        for local_start, local_end, start_tok, end_tok, local_text in pieces:
            children.append(
                Chunk(
                    chunk_id=make_chunk_id(document.document_id, "child", child_index),
                    document_id=document.document_id,
                    chunk_index=child_index,
                    text=local_text,
                    start_char=p_start + local_start,
                    end_char=p_start + local_end,
                    parent_id=parent_id,
                    level=1,
                    start_token=start_tok,
                    end_token=end_tok,
                    metadata={"kind": "child", "strategy": "parent_child"},
                )
            )
            child_index += 1

    return parents, children
