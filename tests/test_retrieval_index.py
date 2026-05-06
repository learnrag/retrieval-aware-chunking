"""Tests for embedding, exact search, and index persistence."""

from pathlib import Path

import numpy as np
import pytest

from chunker.embedding.mock import MockEmbedder
from chunker.models import Chunk, Document
from chunker.retrieval.exact_search import top_k_search
from chunker.storage.index import load_index, save_index


def _child(doc: str, idx: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=f"{doc}_child_{idx:04d}",
        document_id=doc,
        chunk_index=idx,
        text=text,
        start_char=0,
        end_char=len(text),
    )


def test_top_k_tie_break_by_chunk_id():
    embedder = MockEmbedder(dimension=16, seed=1)
    # Identical texts -> identical vectors -> tie broken by chunk_id
    children = [_child("doc", 1, "same"), _child("doc", 0, "same")]
    matrix = embedder.embed_documents([c.text for c in children])
    query = embedder.embed_query("same")
    hits = top_k_search(query, matrix, children, top_k=2, normalized=True)
    assert [h[0].chunk_id for h in hits] == ["doc_child_0000", "doc_child_0001"]


def test_top_k_rejects_invalid():
    with pytest.raises(ValueError, match="top_k"):
        top_k_search(np.zeros(4), np.zeros((0, 4)), [], top_k=0)


def test_index_save_reload(tmp_path: Path):
    embedder = MockEmbedder(dimension=8)
    children = [_child("d", 0, "alpha"), _child("d", 1, "beta")]
    parents = [
        Chunk(
            chunk_id="d_parent_0000",
            document_id="d",
            chunk_index=0,
            text="alpha beta",
            start_char=0,
            end_char=10,
        )
    ]
    docs = [Document(document_id="d", source="d.md", text="alpha beta")]
    emb = embedder.embed_documents([c.text for c in children])
    model_meta = {
        "model": embedder.model_name,
        "dimension": embedder.dimension,
        "normalize": embedder.normalize,
    }
    save_index(
        tmp_path / "index",
        children=children,
        parents=parents,
        documents=docs,
        embeddings=emb,
        model_meta=model_meta,
        config={"chunking": {"strategy": "direct"}},
    )
    loaded = load_index(tmp_path / "index", expected_model=model_meta)
    assert len(loaded.children) == 2
    assert "d_parent_0000" in loaded.parents
    assert loaded.embeddings.shape == (2, 8)

    query = embedder.embed_query("alpha")
    a = top_k_search(query, emb, children, top_k=1, normalized=True)
    b = top_k_search(query, loaded.embeddings, loaded.children, top_k=1, normalized=True)
    assert a[0][0].chunk_id == b[0][0].chunk_id


def test_model_mismatch(tmp_path: Path):
    embedder = MockEmbedder(dimension=8)
    children = [_child("d", 0, "x")]
    emb = embedder.embed_documents(["x"])
    model_meta = {
        "model": embedder.model_name,
        "dimension": 8,
        "normalize": True,
    }
    save_index(
        tmp_path / "index",
        children=children,
        parents=[],
        documents=[],
        embeddings=emb,
        model_meta=model_meta,
        config={},
    )
    with pytest.raises(ValueError, match="dimension"):
        load_index(
            tmp_path / "index",
            expected_model={"model": embedder.model_name, "dimension": 16, "normalize": True},
        )
