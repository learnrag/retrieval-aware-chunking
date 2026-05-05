"""Local Sentence Transformers embedder."""

from __future__ import annotations

import numpy as np

from chunker.embedding.base import Embedder, validate_embeddings


class SentenceTransformerEmbedder(Embedder):
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        *,
        normalize: bool = True,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required. "
                "Install with: pip install 'retrieval-aware-chunker[embed]'"
            ) from exc

        self._model = SentenceTransformer(model_name)
        self._model_name = model_name
        self._normalize = normalize
        probe = self._model.encode(["dimension probe"], normalize_embeddings=False)
        self._dimension = int(np.asarray(probe).shape[-1])
        self._has_query_doc = hasattr(self._model, "encode_query") and hasattr(
            self._model, "encode_document"
        )

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def normalize(self) -> bool:
        return self._normalize

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dimension), dtype=np.float32)
        if self._has_query_doc:
            matrix = np.asarray(
                self._model.encode_document(
                    texts,
                    normalize_embeddings=self._normalize,
                    show_progress_bar=False,
                ),
                dtype=np.float32,
            )
        else:
            matrix = np.asarray(
                self._model.encode(
                    texts,
                    normalize_embeddings=self._normalize,
                    show_progress_bar=False,
                ),
                dtype=np.float32,
            )
        return validate_embeddings(matrix, len(texts))

    def embed_query(self, text: str) -> np.ndarray:
        if self._has_query_doc:
            vector = np.asarray(
                self._model.encode_query(
                    text,
                    normalize_embeddings=self._normalize,
                    show_progress_bar=False,
                ),
                dtype=np.float32,
            )
        else:
            vector = np.asarray(
                self._model.encode(
                    text,
                    normalize_embeddings=self._normalize,
                    show_progress_bar=False,
                ),
                dtype=np.float32,
            )
        if vector.ndim == 2:
            vector = vector[0]
        return validate_embeddings(vector.reshape(1, -1), 1)[0]
