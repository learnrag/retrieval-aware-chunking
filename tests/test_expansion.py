"""Tests for expansion, dedupe, and budget."""

from chunker.expansion.budget import apply_budget
from chunker.expansion.dedupe import dedupe_contexts
from chunker.expansion.window import merge_overlapping_windows
from chunker.models import Document
from chunker.results import ExpandedContext, RetrievedChild
from chunker.expansion.parent import expand_parents
from chunker.models import Chunk


def test_duplicate_parent_elimination():
    parents = {
        "p1": Chunk(
            chunk_id="p1",
            document_id="d",
            chunk_index=0,
            text="PARENT",
            start_char=0,
            end_char=6,
        )
    }
    retrieved = [
        RetrievedChild("c1", 0.9, "a", "d", parent_id="p1"),
        RetrievedChild("c2", 0.8, "b", "d", parent_id="p1"),
    ]
    docs = {"d": Document("d", "d.md", "PARENT")}
    ctx = expand_parents(retrieved, parents, docs)
    deduped = dedupe_contexts(ctx)
    assert len(deduped) == 1
    assert set(deduped[0].derived_from) == {"c1", "c2"}


def test_overlap_merge():
    windows = [
        ExpandedContext("w1", "d", "d.md", "AB", ["c1"], 0, 2, {"sentence_start": 0, "sentence_end": 2}),
        ExpandedContext("w2", "d", "d.md", "BCD", ["c2"], 1, 4, {"sentence_start": 1, "sentence_end": 3}),
    ]
    merged = merge_overlapping_windows(windows)
    assert len(merged) == 1
    assert set(merged[0].derived_from) == {"c1", "c2"}


def test_budget_stops_before_oversize():
    contexts = [
        ExpandedContext("a", "d", "s", "aaaa", ["c1"]),
        ExpandedContext("b", "d", "s", "bbbbbb", ["c2"]),
    ]
    selected, budget = apply_budget(contexts, max_context_chars=5)
    assert [c.context_id for c in selected] == ["a"]
    assert budget["returned_chars"] == 4
    assert budget["items_returned"] == 1


def test_budget_rejects_nonpositive():
    import pytest

    with pytest.raises(ValueError):
        apply_budget([], max_context_chars=0)
