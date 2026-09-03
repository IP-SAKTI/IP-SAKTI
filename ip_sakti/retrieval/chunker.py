"""
ip_sakti.retrieval.chunker — Knowledge document chunking component.

Splits full KnowledgeDocument instances into smaller, overlapping chunks
suitable for dense and sparse indexing, while strictly preserving full
provenance and administrative metadata on every chunk.
"""

from __future__ import annotations

import logging
from typing import Sequence

from ip_sakti.models.document import KnowledgeDocument

logger = logging.getLogger(__name__)


class DocumentChunker:
    """
    Splits KnowledgeDocument objects into fixed-size character/word chunks.

    Parameters
    ----------
    chunk_size :
        Target character length of each chunk.
    chunk_overlap :
        Character overlap between consecutive chunks.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        """Initialise chunker with target size and overlap."""
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap cannot be negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than "
                f"chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: KnowledgeDocument) -> list[KnowledgeDocument]:
        """
        Split a single KnowledgeDocument into a list of chunk KnowledgeDocuments.

        If the document content is shorter than or equal to `chunk_size`, a single
        chunk copy is returned with chunk_index = 0.

        Parameters
        ----------
        doc :
            The parent KnowledgeDocument to split.

        Returns
        -------
        list[KnowledgeDocument]
            A list of chunk KnowledgeDocument instances with inherited metadata.
        """
        text = doc.content.strip()
        if not text:
            logger.warning(
                "Skipping empty document during chunking",
                extra={"doc_id": doc.doc_id},
            )
            return []

        if len(text) <= self.chunk_size:
            chunk = KnowledgeDocument(
                doc_id=f"{doc.doc_id}_chunk_0",
                title=doc.title,
                content=text,
                metadata=doc.metadata.model_copy(deep=True),
                tags=list(doc.tags),
                chunk_index=0,
                parent_doc_id=doc.doc_id,
            )
            return [chunk]

        chunks: list[KnowledgeDocument] = []
        step = self.chunk_size - self.chunk_overlap
        start = 0
        chunk_idx = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk = KnowledgeDocument(
                    doc_id=f"{doc.doc_id}_chunk_{chunk_idx}",
                    title=f"{doc.title} (Part {chunk_idx + 1})",
                    content=chunk_text,
                    metadata=doc.metadata.model_copy(deep=True),
                    tags=list(doc.tags),
                    chunk_index=chunk_idx,
                    parent_doc_id=doc.doc_id,
                )
                chunks.append(chunk)
                chunk_idx += 1

            start += step

        logger.debug(
            "Document chunked successfully",
            extra={
                "parent_doc_id": doc.doc_id,
                "num_chunks": len(chunks),
            },
        )
        return chunks

    def chunk_documents(
        self, docs: Sequence[KnowledgeDocument]
    ) -> list[KnowledgeDocument]:
        """
        Split a sequence of KnowledgeDocuments into a flat list of chunk documents.

        Parameters
        ----------
        docs :
            Sequence of KnowledgeDocument objects.

        Returns
        -------
        list[KnowledgeDocument]
            Flattened list of chunk KnowledgeDocuments.
        """
        all_chunks: list[KnowledgeDocument] = []
        for doc in docs:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
