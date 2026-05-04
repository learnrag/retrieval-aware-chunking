"""Whitespace/token helpers for deterministic chunk sizing."""

from __future__ import annotations


def tokenize_whitespace(text: str) -> list[tuple[int, int, str]]:
    """Return (start_char, end_char, token) spans for whitespace-separated tokens."""
    spans: list[tuple[int, int, str]] = []
    i = 0
    n = len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        start = i
        while i < n and not text[i].isspace():
            i += 1
        spans.append((start, i, text[start:i]))
    return spans


def char_window_for_tokens(
    token_spans: list[tuple[int, int, str]], start_tok: int, end_tok: int
) -> tuple[int, int]:
    """Inclusive-exclusive token range -> character offsets."""
    if start_tok >= end_tok or not token_spans:
        return 0, 0
    start_char = token_spans[start_tok][0]
    end_char = token_spans[end_tok - 1][1]
    return start_char, end_char
