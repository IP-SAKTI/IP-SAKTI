"""
ip_sakti.retrieval.bm25_store — BM25 sparse keyword store.

Manages in-memory and disk-persisted BM25 keyword index using rank_bm25.BM25Okapi.
Approved per AGENTS.md §4: Sparse retrieval backend must be rank_bm25.
"""

from __future__ import annotations

import json
import logging
import pickle
import re
from pathlib import Path
from typing import Sequence

from rank_bm25 import BM25Okapi

from ip_sakti.models.document import KnowledgeDocument
from ip_sakti.retrieval.exceptions import (
    CorruptIndexError,
    EmptyKnowledgeBaseError,
    IndexNotFoundError,
    RetrievalError,
)

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    """Simple lowercasing and word-boundary tokenizer for BM25."""
    return re.findall(r"\w+", text.lower())


class BM25SparseStore:
    """
    BM25 sparse keyword index manager.

    Builds, searches, and persists a BM25Okapi index over document chunks.
    """

    def __init__(self) -> None:
        """Initialise an empty BM25 store."""
        self._bm25: BM25Okapi | None = None
        self._chunks: list[KnowledgeDocument] = []

    @property
    def is_built(self) -> bool:
        """Return True if an active BM25 index is loaded and populated."""
        return self._bm25 is not None and len(self._chunks) > 0

    @property
    def num_documents(self) -> int:
        """Return number of documents in the BM25 index."""
        return len(self._chunks)

    def build_index(self, chunks: Sequence[KnowledgeDocument]) -> None:
        """
        Build BM25 index from document chunks.

        Parameters
        ----------
        chunks :
            List of KnowledgeDocument chunks.

        Raises
        ------
        EmptyKnowledgeBaseError
            If chunks list is empty.
        """
        if not chunks:
            raise EmptyKnowledgeBaseError("Cannot build BM25 index from empty chunk list.")

        corpus_tokens = [_tokenize(chunk.content) for chunk in chunks]

        self._bm25 = BM25Okapi(corpus_tokens)
        self._chunks = list(chunks)

        logger.info(
            "BM25 index built successfully",
            extra={"num_documents": len(chunks)},
        )

    def search(
        self,
        query_text: str,
        top_k: int = 20,
    ) -> list[tuple[KnowledgeDocument, float]]:
        """
        Perform BM25 sparse keyword search for a query string.

        Parameters
        ----------
        query_text :
            Raw or normalized user query string.
        top_k :
            Maximum number of document chunks to retrieve.

        Returns
        -------
        list[tuple[KnowledgeDocument, float]]
            List of (chunk, bm25_score) pairs, sorted by score descending.
        """
        if not self.is_built or self._bm25 is None:
            logger.warning("BM25 search called on empty or unbuilt index.")
            return []

        if top_k <= 0:
            return []

        query_tokens = _tokenize(query_text)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:top_k]

        results: list[tuple[KnowledgeDocument, float]] = []
        for idx in top_indices:
            score = float(scores[idx])
            # Exclude non-matching chunks (BM25 score <= 0.0) if desired,
            # or keep top_k candidates with non-zero scores
            if score > 0.0:
                results.append((self._chunks[idx], score))

        return results

    def save(self, dir_path: str | Path) -> None:
        """
        Save BM25 index and document metadata to dir_path.

        Parameters
        ----------
        dir_path :
            Target directory path.
        """
        if not self.is_built or self._bm25 is None:
            raise RetrievalError("Cannot save unbuilt BM25 index.")

        target_dir = Path(dir_path)
        target_dir.mkdir(parents=True, exist_ok=True)

        bm25_file = target_dir / "bm25.pkl"
        meta_file = target_dir / "bm25_meta.json"

        try:
            with bm25_file.open("wb") as fh:
                pickle.dump(self._bm25, fh, protocol=pickle.HIGHEST_PROTOCOL)

            meta_data = [chunk.model_dump(mode="json") for chunk in self._chunks]
            with meta_file.open("w", encoding="utf-8") as fh:
                json.dump(meta_data, fh, indent=2, ensure_ascii=False)

            logger.info("Saved BM25 index to disk", extra={"dir": str(target_dir)})
        except Exception as exc:
            raise RetrievalError(f"Failed to save BM25 index to {target_dir}: {exc}") from exc

    def load(self, dir_path: str | Path) -> None:
        """
        Load BM25 index and document metadata from dir_path.

        Parameters
        ----------
        dir_path :
            Source directory path containing bm25.pkl and bm25_meta.json.
        """
        target_dir = Path(dir_path)
        bm25_file = target_dir / "bm25.pkl"
        meta_file = target_dir / "bm25_meta.json"

        if not bm25_file.exists() or not meta_file.exists():
            raise IndexNotFoundError(
                f"BM25 index files missing in directory {target_dir}. "
                f"Expected bm25.pkl and bm25_meta.json."
            )

        try:
            with bm25_file.open("rb") as fh:
                bm25 = pickle.load(fh)  # noqa: S301

            with meta_file.open("r", encoding="utf-8") as fh:
                meta_raw = json.load(fh)

            chunks = [KnowledgeDocument.model_validate(item) for item in meta_raw]

            if not isinstance(bm25, BM25Okapi):
                raise CorruptIndexError("bm25.pkl does not contain a valid BM25Okapi instance.")

            if len(chunks) != bm25.corpus_size:
                raise CorruptIndexError(
                    f"BM25 corpus size ({bm25.corpus_size}) does not match "
                    f"metadata count ({len(chunks)})."
                )

            self._bm25 = bm25
            self._chunks = chunks
            logger.info("Loaded BM25 index from disk", extra={"dir": str(target_dir)})
        except IndexNotFoundError:
            raise
        except Exception as exc:
            raise CorruptIndexError(
                f"Failed to load or parse BM25 index from {target_dir}: {exc}"
            ) from exc
