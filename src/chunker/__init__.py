"""Package exports."""

from chunker.embedding import Embedder, MockEmbedder
from chunker.models import Chunk, Document
from chunker.pipeline import build_index, search

__all__ = [
    "Chunk",
    "Document",
    "Embedder",
    "MockEmbedder",
    "build_index",
    "search",
]
__version__ = "0.1.0"
