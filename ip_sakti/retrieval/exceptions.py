"""
ip_sakti.retrieval.exceptions — Custom exceptions for the Hybrid RAG layer.

Raised when indexing, vector storage, sparse search, reranking, or pipeline execution fails.
"""

from __future__ import annotations


class RetrievalError(Exception):
    """Base exception for all retrieval-related errors."""


class IndexNotFoundError(RetrievalError):
    """Raised when FAISS or BM25 index files do not exist on disk."""


class CorruptIndexError(RetrievalError):
    """Raised when an index file exists but cannot be deserialised or read."""


class EmptyKnowledgeBaseError(RetrievalError):
    """Raised when attempting to build an index from an empty list of documents."""
