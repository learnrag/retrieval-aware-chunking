"""Local index persistence: chunks, embeddings, and compatibility metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from chunker.io import read_json, read_jsonl, write_json, write_jsonl
from chunker.models import SCHEMA_VERSION, Chunk, Document


@dataclass
class IndexPaths:
    root: Path

    @property
    def manifest(self) -> Path:
        return self.root / "manifest.json"

    @property
    def chunks(self) -> Path:
        return self.root / "chunks.jsonl"

    @property
    def parents(self) -> Path:
        return self.root / "parents.jsonl"

    @property
    def documents(self) -> Path:
        return self.root / "documents.jsonl"

    @property
    def embeddings(self) -> Path:
        return self.root / "embeddings.npy"

    @property
    def model(self) -> Path:
        return self.root / "model.json"

    @property
    def config(self) -> Path:
        return self.root / "config.json"


@dataclass
class LoadedIndex:
    paths: IndexPaths
    children: list[Chunk]
    parents: dict[str, Chunk]
    documents: dict[str, Document]
    embeddings: np.ndarray
    model_meta: dict[str, Any]
    config: dict[str, Any]
    manifest: dict[str, Any]


def save_index(
    root: Path,
    *,
    children: list[Chunk],
    parents: list[Chunk],
    documents: list[Document],
    embeddings: np.ndarray,
    model_meta: dict[str, Any],
    config: dict[str, Any],
) -> IndexPaths:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    paths = IndexPaths(root)

    if embeddings.ndim != 2 or embeddings.shape[0] != len(children):
        raise ValueError("embeddings rows must match children count")

    write_jsonl(paths.chunks, [c.to_dict() for c in children])
    write_jsonl(paths.parents, [p.to_dict() for p in parents])
    write_jsonl(paths.documents, [d.to_dict() for d in documents])
    np.save(paths.embeddings, embeddings.astype(np.float32))
    write_json(paths.model, model_meta)
    write_json(paths.config, config)
    write_json(
        paths.manifest,
        {
            "schema_version": SCHEMA_VERSION,
            "child_count": len(children),
            "parent_count": len(parents),
            "document_count": len(documents),
            "embedding_dim": int(embeddings.shape[1]) if embeddings.size else 0,
        },
    )
    return paths


def load_index(root: Path, *, expected_model: dict[str, Any] | None = None) -> LoadedIndex:
    root = Path(root)
    paths = IndexPaths(root)
    if not paths.manifest.is_file():
        raise FileNotFoundError(
            f"Missing index at {root}. Build one with: chunker build <data_dir>"
        )

    try:
        manifest = read_json(paths.manifest)
        model_meta = read_json(paths.model)
        config = read_json(paths.config)
        child_rows = read_jsonl(paths.chunks)
        parent_rows = read_jsonl(paths.parents) if paths.parents.is_file() else []
        doc_rows = read_jsonl(paths.documents) if paths.documents.is_file() else []
        embeddings = np.load(paths.embeddings)
    except (OSError, ValueError) as exc:
        raise ValueError(f"Corrupt index artifact under {root}: {exc}") from exc

    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"Index schema {manifest.get('schema_version')!r} incompatible with "
            f"{SCHEMA_VERSION!r}"
        )

    if expected_model is not None:
        _check_model_compat(model_meta, expected_model)

    if embeddings.ndim != 2:
        raise ValueError("embeddings.npy must be 2-D")
    children = [Chunk.from_dict(r) for r in child_rows]
    if embeddings.shape[0] != len(children):
        raise ValueError("embeddings row count does not match chunks.jsonl")

    parents = {}
    for r in parent_rows:
        p = Chunk.from_dict(r)
        parents[p.chunk_id] = p

    documents = {}
    for r in doc_rows:
        documents[r["document_id"]] = Document(
            document_id=r["document_id"],
            source=r["source"],
            text=r["text"],
            metadata=dict(r.get("metadata") or {}),
        )

    return LoadedIndex(
        paths=paths,
        children=children,
        parents=parents,
        documents=documents,
        embeddings=embeddings.astype(np.float32),
        model_meta=model_meta,
        config=config,
        manifest=manifest,
    )


def _check_model_compat(stored: dict[str, Any], expected: dict[str, Any]) -> None:
    if stored.get("model") != expected.get("model"):
        raise ValueError(
            f"Model mismatch: index={stored.get('model')!r} query={expected.get('model')!r}"
        )
    if int(stored.get("dimension", -1)) != int(expected.get("dimension", -2)):
        raise ValueError(
            f"Embedding dimension mismatch: index={stored.get('dimension')} "
            f"query={expected.get('dimension')}"
        )
    if bool(stored.get("normalize")) != bool(expected.get("normalize")):
        raise ValueError("Normalize flag mismatch between index and query embedder")
