"""Tests for chunking strategies."""

from chunker.chunking import build_chunks
from chunker.chunking.sentence_window import expand_window_from_document, split_sentences
from chunker.models import Document


SAMPLE = """# Database Backups
Production databases are backed up every 6 hours.
Backups are retained for 30 days.
Restore requests require approval.
"""


def _doc(text: str = SAMPLE, doc_id: str = "doc1") -> Document:
    return Document(document_id=doc_id, source="sample.md", text=text)


def test_direct_chunk_ids_stable():
    _, children = build_chunks(_doc(), "direct", child_size_tokens=8, overlap_tokens=0)
    assert children[0].chunk_id == "doc1_child_0000"
    assert all(c.parent_id is None for c in children)


def test_parent_child_links():
    parents, children = build_chunks(
        _doc(), "parent_child", child_size_tokens=8, parent_size_tokens=64, overlap_tokens=0
    )
    assert parents
    assert children
    assert all(c.parent_id for c in children)
    assert all(c.parent_id in {p.chunk_id for p in parents} for c in children)
    assert any("every 6 hours" in c.text for c in children)


def test_sentence_split_and_window_edges():
    doc = _doc()
    spans = split_sentences(doc.text)
    assert len(spans) >= 3
    _, sentences = build_chunks(doc, "sentence_window")
    # First sentence window clamps to start
    start, end, text, _, _ = expand_window_from_document(doc.text, sentences, 0, 2)
    assert start == 0
    assert "every 6 hours" in text or "Database" in text
    # Last sentence window clamps to end
    last = len(sentences) - 1
    start, end, text, _, _ = expand_window_from_document(doc.text, sentences, last, 2)
    assert end == len(sentences)
    assert "approval" in text
