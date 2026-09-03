"""
ip_sakti.retrieval.faiss_store — FAISS dense vector store.

Manages in-memory and disk-persisted FAISS vector index (faiss-cpu) for dense
similarity search. Uses IndexFlatIP over unit-normalized vector embeddings to
compute exact cosine similarity.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Sequence

import faiss
import numpy as np

from ip_sakti.models.document import KnowledgeDocument
from ip_sakti.retrieval.exceptions import (
    CorruptIndexError,
    EmptyKnowledgeBaseError,
    IndexNotFoundError,
    RetrievalError,
)

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """
    FAISS dense vector index manager.

    Maps FAISS integer IDs (0..N-1) to KnowledgeDocument chunk objects and
    handles persistence to/from disk.
    """

    def __init__(self) -> None:
        """Initialise an empty FAISS vector store."""
        self._index: faiss.IndexFlatIP | None = None
        self._chunks: list[KnowledgeDocument] = []

    @property
    def is_built(self) -> bool:
        """Return True if an active FAISS index is loaded and populated."""
        return self._index is not None and len(self._chunks) > 0

    @property
    def num_vectors(self) -> int:
        """Return number of vectors in the FAISS index."""
        return self._index.ntotal if self._index is not None else 0

    def build_index(
        self,
        chunks: Sequence[KnowledgeDocument],
        embeddings: np.ndarray,
    ) -> None:
        """
        Build FAISS index from document chunks and vector embeddings.

        Parameters
        ----------
        chunks :
            List of KnowledgeDocument chunks.
        embeddings :
            2D numpy float32 array of shape (N, dim).

        Raises
        ------
        EmptyKnowledgeBaseError
            If chunks or embeddings are empty.
        RetrievalError
            If chunk count does not match embedding count or array is invalid.
        """
        if not chunks:
            raise EmptyKnowledgeBaseError("Cannot build FAISS index from empty chunk list.")
        if embeddings.size == 0 or embeddings.ndim != 2:
            raise EmptyKnowledgeBaseError("Embeddings array is empty or has invalid shape.")
        if len(chunks) != embeddings.shape[0]:
            raise RetrievalError(
                f"Mismatch between chunks count ({len(chunks)}) and "
                f"embeddings count ({embeddings.shape[0]})."
            )

        num_samples, dim = embeddings.shape
        embeddings_f32 = np.ascontiguousarray(embeddings, dtype=np.float32)

        index = faiss.IndexFlatIP(dim)
        index.add(embeddings_f32)

        self._index = index
        self._chunks = list(chunks)

        logger.info(
            "FAISS index built successfully",
            extra={"num_vectors": num_samples, "dimension": dim},
        )

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 20,
    ) -> list[tuple[KnowledgeDocument, float]]:
        """
        Perform dense k-NN search using inner product / cosine similarity.

        Parameters
        ----------
        query_vector :
            1D or 2D float32 numpy array representing the query embedding.
        top_k :
            Maximum number of nearest neighbors to retrieve.

        Returns
        -------
        list[tuple[KnowledgeDocument, float]]
            List of (chunk, cosine_similarity_score) pairs, sorted descending.
        """
        if not self.is_built or self._index is None:
            logger.warning("FAISS search called on empty or unbuilt index.")
            return []

        if top_k <= 0:
            return []

        # Prepare query vector
        q_arr = np.ascontiguousarray(query_vector, dtype=np.float32)
        if q_arr.ndim == 1:
            q_arr = q_arr.reshape(1, -1)

        if q_arr.shape[1] != self._index.d:
            raise RetrievalError(
                f"Query vector dimension ({q_arr.shape[1]}) does not match "
                f"FAISS index dimension ({self._index.d})."
            )

        actual_k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(q_arr, actual_k)

        results: list[tuple[KnowledgeDocument, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            results.append((self._chunks[idx], float(score)))

        return results

    def save(self, dir_path: str | Path) -> None:
        """
        Save FAISS index binary and metadata JSON to dir_path.

        Parameters
        ----------
        dir_path :
            Target directory path.
        """
        if not self.is_built or self._index is None:
            raise RetrievalError("Cannot save unbuilt FAISS index.")

        target_dir = Path(dir_path)
        target_dir.mkdir(parents=True, exist_ok=True)

        index_file = target_dir / "faiss.index"
        meta_file = target_dir / "faiss_meta.json"

        try:
            faiss.write_index(self._index, str(index_file))
            meta_data = [chunk.model_dump(mode="json") for chunk in self._chunks]
            with meta_file.open("w", encoding="utf-8") as fh:
                json.dump(meta_data, fh, indent=2, ensure_ascii=False)
            logger.info("Saved FAISS index to disk", extra={"dir": str(target_dir)})
        except Exception as exc:
            raise RetrievalError(f"Failed to save FAISS index to {target_dir}: {exc}") from exc

    def load(self, dir_path: str | Path) -> None:
        """
        Load FAISS index binary and metadata JSON from dir_path.

        Parameters
        ----------
        dir_path :
            Source directory path containing faiss.index and faiss_meta.json.
        """
        target_dir = Path(dir_path)
        index_file = target_dir / "faiss.index"
        meta_file = target_dir / "faiss_meta.json"

        if not index_file.exists() or not meta_file.exists():
            raise IndexNotFoundError(
                f"FAISS index files missing in directory {target_dir}. "
                f"Expected faiss.index and faiss_meta.json."
            )

        try:
            index = faiss.read_index(str(index_file))
            with meta_file.open("r", encoding="utf-8") as fh:
                meta_raw = json.load(fh)

            chunks = [KnowledgeDocument.model_validate(item) for item in meta_raw]

            if index.ntotal != len(chunks):
                raise CorruptIndexError(
                    f"FAISS index count ({index.ntotal}) does not match "
                    f"metadata count ({len(chunks)})."
                )

            self._index = index
            self._chunks = chunks
            logger.info("Loaded FAISS index from disk", extra={"dir": str(target_dir)})
        except IndexNotFoundError:
            raise
        except Exception as exc:
            raise CorruptIndexError(
                f"Failed to load or parse FAISS index from {target_dir}: {exc}"
            ) from exc
