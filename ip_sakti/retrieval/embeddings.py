"""
ip_sakti.retrieval.embeddings — Multilingual embedding generator component.

Wraps sentence-transformers to generate dense vector embeddings for documents
and user queries.  Vectors are normalized to unit L2 norm so that FAISS inner
product search directly computes cosine similarity.

Approved per AGENTS.md §5: Preferred pretrained embedding model is sentence-transformers.
Model name is read from config/settings.yaml models.embedding_model.
"""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from ip_sakti.retrieval.exceptions import RetrievalError
from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates normalized dense embeddings using SentenceTransformer.

    Parameters
    ----------
    model_name :
        HuggingFace model identifier. Defaults to models.embedding_model
        from config/settings.yaml.
    """

    def __init__(self, model_name: str | None = None) -> None:
        """Initialise embedding model using config or explicit parameter."""
        if model_name is not None:
            self.model_name = model_name
        else:
            cfg = get_settings()
            self.model_name = cfg.get("models", {}).get(
                "embedding_model",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )

        self._model: SentenceTransformer | None = None
        logger.debug(
            "EmbeddingGenerator initialised",
            extra={"model_name": self.model_name},
        )

    def _get_model(self) -> SentenceTransformer:
        """Lazy load the SentenceTransformer model on first use."""
        if self._model is None:
            try:
                logger.info(
                    "Loading SentenceTransformer model",
                    extra={"model_name": self.model_name},
                )
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                raise RetrievalError(
                    f"Failed to load embedding model {self.model_name!r}: {exc}"
                ) from exc
        return self._model

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        """
        Generate L2-normalized float32 embeddings for a sequence of text strings.

        Parameters
        ----------
        texts :
            List or sequence of strings to embed.

        Returns
        -------
        np.ndarray
            2D float32 numpy array of shape (len(texts), dimension).
            Empty array of shape (0, dim) if texts is empty.
        """
        if not texts:
            # Return empty array with dimension 0 or model dimension if loaded
            dim = self.dimension if self._model is not None else 384
            return np.empty((0, dim), dtype=np.float32)

        clean_texts = [t.strip() for t in texts]
        model = self._get_model()

        try:
            embeddings = model.encode(
                clean_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings.astype(np.float32)
        except Exception as exc:
            raise RetrievalError(
                f"Embedding generation failed for {len(texts)} texts: {exc}"
            ) from exc

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate L2-normalized float32 embedding for a single query string.

        Parameters
        ----------
        query :
            Query text string.

        Returns
        -------
        np.ndarray
            1D float32 array of shape (dimension,).
        """
        stripped = query.strip()
        if not stripped:
            raise RetrievalError("Cannot generate embedding for empty query.")

        arr = self.embed_texts([stripped])
        return arr[0]

    @property
    def dimension(self) -> int:
        """Return the vector embedding dimension of the loaded model."""
        model = self._get_model()
        dim = model.get_sentence_embedding_dimension()
        return int(dim) if dim is not None else 384
