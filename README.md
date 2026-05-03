# Retrieval-Aware Chunker

Standalone local system that retrieves small child chunks, then expands them into parent sections or sentence windows. No LLM generation.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"
```

Use `pip install -e ".[dev]"` plus `--mock` to skip the embedding model download.

## Quick start

```bash
chunker build ./data --strategy parent-child --mock
chunker search "How often are production databases backed up?" --mock
chunker evaluate ./benchmarks/retrieval.json --mock
chunker compare ./benchmarks/retrieval.json --strategies direct,parent,sentence-window --mock
```

## Library

```python
from chunker.pipeline import build_index, search
from chunker.embedding.mock import MockEmbedder

embedder = MockEmbedder()
build_index("./data", "./index", embedder=embedder, strategy="parent_child")
result = search("backup policy", "./index", embedder=embedder, top_k=5)
```

## HTTP API

```bash
chunker-api
# GET  /health
# POST /build
# POST /search
# POST /inspect
```

## Docker

```bash
docker compose up --build
```

## Tests

```bash
pytest
pytest -m integration  # real sentence-transformers model
```

## Scope

In: child/parent chunking, sentence-window expansion, local embeddings, exact cosine search, evaluation.

Out: LLM answers, rerankers, hybrid BM25, ANN indexes, cloud vector DBs.
