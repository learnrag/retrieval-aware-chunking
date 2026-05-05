"""Sentence segmentation and sentence-window retrieval units."""

from __future__ import annotations

import re

from chunker.models import Chunk, Document, make_chunk_id

# Deterministic sentence splitter: split after .!? followed by whitespace.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Return (start_char, end_char, sentence_text) with offsets into ``text``."""
    if not text.strip():
        return []

    parts = _SENTENCE_RE.split(text)
    spans: list[tuple[int, int, str]] = []
    search_from = 0
    for part in parts:
        if part == "":
            continue
        idx = text.find(part, search_from)
        if idx < 0:
            idx = search_from
        start = idx
        end = idx + len(part)
        spans.append((start, end, text[start:end]))
        search_from = end

    if not spans and text.strip():
        return [(0, len(text), text)]
    return spans


def chunk_sentences(document: Document) -> list[Chunk]:
    """Index each sentence as a retrieval child; store sentence_index in metadata."""
    spans = split_sentences(document.text)
    chunks: list[Chunk] = []
    for idx, (start, end, sent) in enumerate(spans):
        chunks.append(
            Chunk(
                chunk_id=make_chunk_id(document.document_id, "child", idx),
                document_id=document.document_id,
                chunk_index=idx,
                text=sent,
                start_char=start,
                end_char=end,
                parent_id=None,
                level=0,
                metadata={
                    "kind": "sentence",
                    "strategy": "sentence_window",
                    "sentence_index": idx,
                    "sentence_count": len(spans),
                },
            )
        )
    return chunks


def expand_window_from_document(
    document_text: str,
    sentences: list[Chunk],
    center_index: int,
    window_size: int,
) -> tuple[int, int, str, int, int]:
    """Clamp window and slice original document text for faithful context."""
    if window_size < 0:
        raise ValueError("window_size must be >= 0")
    if not sentences:
        raise ValueError("no sentences to expand")
    if center_index < 0 or center_index >= len(sentences):
        raise ValueError("center_index out of range")

    start = max(0, center_index - window_size)
    end = min(len(sentences), center_index + window_size + 1)
    start_char = sentences[start].start_char
    end_char = sentences[end - 1].end_char
    return start, end, document_text[start_char:end_char], start_char, end_char
