"""Unit tests for models and ingestion."""

from pathlib import Path

import pytest

from chunker.ingest import ingest_directory, ingest_file, normalize_text
from chunker.models import Chunk, make_chunk_id


def test_normalize_text_newlines():
    assert normalize_text("a\r\nb\rc") == "a\nb\nc"


def test_make_chunk_id_stable():
    assert make_chunk_id("doc1", "child", 7) == "doc1_child_0007"
    assert make_chunk_id("doc1", "parent", 2) == "doc1_parent_0002"


def test_chunk_roundtrip():
    chunk = Chunk(
        chunk_id="doc1_child_0000",
        document_id="doc1",
        chunk_index=0,
        text="hello",
        start_char=0,
        end_char=5,
        parent_id="doc1_parent_0000",
        level=1,
    )
    restored = Chunk.from_dict(chunk.to_dict())
    assert restored == chunk


def test_ingest_file(tmp_path: Path):
    path = tmp_path / "sample.md"
    path.write_text("# Title\nBody text.\n", encoding="utf-8")
    doc = ingest_file(path)
    assert doc.document_id == "sample"
    assert doc.text.startswith("# Title")
    assert "Title" in doc.text


def test_ingest_rejects_unsupported(tmp_path: Path):
    path = tmp_path / "x.pdf"
    path.write_bytes(b"%PDF")
    with pytest.raises(ValueError, match="Unsupported"):
        ingest_file(path)


def test_ingest_directory(tmp_path: Path):
    (tmp_path / "a.md").write_text("alpha", encoding="utf-8")
    (tmp_path / "b.txt").write_text("beta", encoding="utf-8")
    docs = ingest_directory(tmp_path)
    assert {d.document_id for d in docs} == {"a", "b"}
