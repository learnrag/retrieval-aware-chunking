"""Fixed-size child chunking (direct retrieval baseline)."""

from __future__ import annotations

from chunker.chunking.tokens import char_window_for_tokens, tokenize_whitespace
from chunker.models import Chunk, Document, make_chunk_id


def split_text_by_tokens(
    text: str,
    *,
    size_tokens: int,
    overlap_tokens: int = 0,
) -> list[tuple[int, int, int, int, str]]:
    """
    Split text into overlapping token windows.

    Returns list of (start_char, end_char, start_token, end_token, chunk_text).
    """
    if size_tokens < 1:
        raise ValueError("size_tokens must be >= 1")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens must be >= 0")
    if overlap_tokens >= size_tokens:
        raise ValueError("overlap_tokens must be < size_tokens")

    spans = tokenize_whitespace(text)
    if not spans:
        if text.strip() == "":
            return []
        return [(0, len(text), 0, 0, text)]

    step = size_tokens - overlap_tokens
    out: list[tuple[int, int, int, int, str]] = []
    start = 0
    while start < len(spans):
        end = min(start + size_tokens, len(spans))
        start_char, end_char = char_window_for_tokens(spans, start, end)
        # Extend end_char through trailing whitespace until next token or EOS
        # so consecutive chunks cover contiguous source ranges when overlap=0.
        chunk_text = text[start_char:end_char]
        out.append((start_char, end_char, start, end, chunk_text))
        if end >= len(spans):
            break
        start += step
    return out


def chunk_direct(
    document: Document,
    *,
    child_size_tokens: int = 256,
    overlap_tokens: int = 32,
) -> list[Chunk]:
    """Child-only chunks for the direct/fixed baseline."""
    pieces = split_text_by_tokens(
        document.text,
        size_tokens=child_size_tokens,
        overlap_tokens=overlap_tokens,
    )
    chunks: list[Chunk] = []
    for idx, (start_char, end_char, start_tok, end_tok, text) in enumerate(pieces):
        chunks.append(
            Chunk(
                chunk_id=make_chunk_id(document.document_id, "child", idx),
                document_id=document.document_id,
                chunk_index=idx,
                text=text,
                start_char=start_char,
                end_char=end_char,
                parent_id=None,
                level=0,
                start_token=start_tok,
                end_token=end_tok,
                metadata={"kind": "child", "strategy": "direct"},
            )
        )
    return chunks
