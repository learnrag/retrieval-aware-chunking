"""Dispatch chunking strategies."""

from __future__ import annotations

from chunker.chunking.child import chunk_direct
from chunker.chunking.parent import chunk_parent_child
from chunker.chunking.sentence_window import chunk_sentences
from chunker.config import ChunkStrategy
from chunker.models import Chunk, Document


def build_chunks(
    document: Document,
    strategy: ChunkStrategy,
    *,
    child_size_tokens: int = 256,
    parent_size_tokens: int = 1024,
    overlap_tokens: int = 32,
) -> tuple[list[Chunk], list[Chunk]]:
    """
    Return (context_units, retrieval_units).

    For direct: both lists are the same child chunks.
    For parent_child: parents + children.
    For sentence_window: sentences as both (expansion uses neighbors later).
    """
    if strategy == "direct":
        children = chunk_direct(
            document,
            child_size_tokens=child_size_tokens,
            overlap_tokens=overlap_tokens,
        )
        return children, children
    if strategy == "parent_child":
        return chunk_parent_child(
            document,
            child_size_tokens=child_size_tokens,
            parent_size_tokens=parent_size_tokens,
            overlap_tokens=overlap_tokens,
        )
    if strategy == "sentence_window":
        sentences = chunk_sentences(document)
        return sentences, sentences
    raise ValueError(f"Unknown chunking strategy: {strategy}")
