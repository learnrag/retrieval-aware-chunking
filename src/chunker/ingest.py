"""Document ingestion for UTF-8 text and Markdown files."""

from __future__ import annotations

from pathlib import Path

from chunker.models import Document

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown"}


def normalize_text(text: str) -> str:
    """Normalize newlines; keep content otherwise intact."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def load_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    return normalize_text(raw)


def document_id_from_path(path: Path, override: str | None = None) -> str:
    if override is not None:
        return override
    return path.stem


def ingest_file(path: Path, *, document_id: str | None = None) -> Document:
    path = path.resolve()
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Unsupported file type {path.suffix!r}; expected one of {sorted(SUPPORTED_SUFFIXES)}"
        )
    text = load_text(path)
    doc_id = document_id_from_path(path, document_id)
    return Document(
        document_id=doc_id,
        source=str(path),
        text=text,
        metadata={"filename": path.name, "suffix": path.suffix.lower()},
    )


def ingest_directory(directory: Path) -> list[Document]:
    directory = directory.resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f"Not a directory: {directory}")
    paths = sorted(
        p
        for p in directory.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )
    if not paths:
        raise ValueError(f"No .txt/.md files found under {directory}")

    docs: list[Document] = []
    seen_ids: set[str] = set()
    for path in paths:
        doc = ingest_file(path)
        if doc.document_id in seen_ids:
            # Disambiguate duplicate stems from nested paths.
            rel = path.relative_to(directory).as_posix().replace("/", "__")
            doc = Document(
                document_id=Path(rel).stem.replace(".", "_"),
                source=doc.source,
                text=doc.text,
                metadata=doc.metadata,
            )
            if doc.document_id in seen_ids:
                raise ValueError(f"Duplicate document_id after disambiguation: {doc.document_id}")
        seen_ids.add(doc.document_id)
        docs.append(doc)
    return docs
