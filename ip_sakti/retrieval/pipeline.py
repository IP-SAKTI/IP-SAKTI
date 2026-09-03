"""
ip_sakti.retrieval.pipeline — Hybrid RAG retrieval pipeline coordinator.

Coordinates the complete hybrid retrieval workflow:
  Query (normalised/translated from Stage 2)
    │
    ├── FAISS dense search
    └── BM25 sparse search
          │
          ▼
    RRF fusion
          │
          ▼
    Cross-Encoder reranking
          │
          ▼
    Top Evidence (EvidenceChunk list)

Approved per AGENTS.md §3: Hybrid RAG is FAISS + BM25 -> RRF -> Cross-Encoder.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from ip_sakti.models.document import KnowledgeDocument
from ip_sakti.models.query import EvidenceChunk
from ip_sakti.retrieval.bm25_store import BM25SparseStore
from ip_sakti.retrieval.chunker import DocumentChunker
from ip_sakti.retrieval.embeddings import EmbeddingGenerator
from ip_sakti.retrieval.exceptions import RetrievalError
from ip_sakti.retrieval.faiss_store import FAISSVectorStore
from ip_sakti.retrieval.fusion import ReciprocalRankFusion
from ip_sakti.retrieval.reranker import CrossEncoderReranker
from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)


class HybridRAGPipeline:
    """
    Coordinates document chunking, dual indexing (FAISS + BM25), reciprocal rank
    fusion (RRF), and cross-encoder reranking.

    Parameters
    ----------
    chunker :
        Document chunker instance.
    embedding_generator :
        Dense embedding generator instance.
    faiss_store :
        FAISS vector store instance.
    bm25_store :
        BM25 sparse store instance.
    fusion :
        RRF fusion instance.
    reranker :
        Cross-Encoder reranker instance.
    """

    def __init__(
        self,
        chunker: DocumentChunker | None = None,
        embedding_generator: EmbeddingGenerator | None = None,
        faiss_store: FAISSVectorStore | None = None,
        bm25_store: BM25SparseStore | None = None,
        fusion: ReciprocalRankFusion | None = None,
        reranker: CrossEncoderReranker | None = None,
    ) -> None:
        """Initialise pipeline components with optional injections."""
        self.chunker = chunker or DocumentChunker()
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
        self.faiss_store = faiss_store or FAISSVectorStore()
        self.bm25_store = bm25_store or BM25SparseStore()
        self.fusion = fusion or ReciprocalRankFusion()
        self.reranker = reranker or CrossEncoderReranker()

        cfg = get_settings()
        retrieval_cfg = cfg.get("retrieval", {})
        self.faiss_top_k: int = int(retrieval_cfg.get("faiss_top_k", 20))
        self.bm25_top_k: int = int(retrieval_cfg.get("bm25_top_k", 20))
        self.rerank_top_k: int = int(retrieval_cfg.get("rerank_top_k", 5))

        paths_cfg = cfg.get("paths", {})
        self.index_dir: Path = Path(paths_cfg.get("index_dir", "indexes/"))

    @property
    def is_built(self) -> bool:
        """Return True if both FAISS and BM25 indexes are populated."""
        return self.faiss_store.is_built and self.bm25_store.is_built

    def build_index(self, documents: Sequence[KnowledgeDocument]) -> int:
        """
        Chunk documents and build both FAISS and BM25 indexes in memory.

        Parameters
        ----------
        documents :
            List of KnowledgeDocument instances from authoritative knowledge base.

        Returns
        -------
        int
            Number of generated document chunks indexed.
        """
        if not documents:
            logger.warning("Empty document list passed to HybridRAGPipeline.build_index.")
            return 0

        logger.info(
            "Chunking knowledge base documents",
            extra={"doc_count": len(documents)},
        )
        chunks = self.chunker.chunk_documents(documents)
        if not chunks:
            logger.warning("Chunker produced 0 chunks from documents.")
            return 0

        # Extract chunk contents
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings & build FAISS index
        logger.info("Generating embeddings for dense FAISS index", extra={"num_chunks": len(chunks)})
        embeddings = self.embedding_generator.embed_texts(texts)
        self.faiss_store.build_index(chunks, embeddings)

        # Build BM25 index
        logger.info("Building BM25 sparse index", extra={"num_chunks": len(chunks)})
        self.bm25_store.build_index(chunks)

        logger.info(
            "Hybrid RAG index build completed",
            extra={"num_chunks": len(chunks)},
        )
        return len(chunks)

    def save_index(self, dir_path: str | Path | None = None) -> None:
        """
        Save FAISS and BM25 indexes to disk.

        Parameters
        ----------
        dir_path :
            Target directory. Defaults to paths.index_dir from settings.yaml.
        """
        target_dir = Path(dir_path) if dir_path is not None else self.index_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        self.faiss_store.save(target_dir)
        self.bm25_store.save(target_dir)
        logger.info("Saved Hybrid RAG indexes to disk", extra={"dir": str(target_dir)})

    def load_index(self, dir_path: str | Path | None = None) -> None:
        """
        Load FAISS and BM25 indexes from disk.

        Parameters
        ----------
        dir_path :
            Source directory. Defaults to paths.index_dir from settings.yaml.
        """
        source_dir = Path(dir_path) if dir_path is not None else self.index_dir
        self.faiss_store.load(source_dir)
        self.bm25_store.load(source_dir)
        logger.info("Loaded Hybrid RAG indexes from disk", extra={"dir": str(source_dir)})

    def search(
        self,
        query_text: str,
        faiss_top_k: int | None = None,
        bm25_top_k: int | None = None,
        rerank_top_k: int | None = None,
    ) -> list[EvidenceChunk]:
        """
        Run the complete Hybrid RAG pipeline for a normalised/translated query.

        Steps
        -----
        1. Check query text & index availability.
        2. Execute dense search (FAISS) & sparse search (BM25).
        3. Fuse candidate rankings (RRF).
        4. Rerank candidates with Cross-Encoder.
        5. Package top candidates into EvidenceChunk Pydantic models with provenance.

        Parameters
        ----------
        query_text :
            The normalised/translated English query text from Stage 2.
        faiss_top_k :
            Optional override for dense retrieval candidate limit.
        bm25_top_k :
            Optional override for sparse retrieval candidate limit.
        rerank_top_k :
            Optional override for final evidence count.

        Returns
        -------
        list[EvidenceChunk]
            Top reranked evidence chunks carrying provenance metadata and scores.
        """
        clean_query = query_text.strip()
        if not clean_query:
            logger.warning("Empty query passed to HybridRAGPipeline.search.")
            return []

        if not self.is_built:
            # Try auto-loading from index_dir if available on disk
            try:
                self.load_index()
            except Exception:
                logger.warning("Hybrid RAG pipeline search called but index is not loaded/built.")
                return []

        f_top_k = faiss_top_k if faiss_top_k is not None else self.faiss_top_k
        b_top_k = bm25_top_k if bm25_top_k is not None else self.bm25_top_k
        r_top_k = rerank_top_k if rerank_top_k is not None else self.rerank_top_k

        # 1. FAISS dense search
        try:
            query_vector = self.embedding_generator.embed_query(clean_query)
            faiss_results = self.faiss_store.search(query_vector, top_k=f_top_k)
        except Exception as exc:
            logger.error(f"FAISS dense search failed: {exc}")
            faiss_results = []

        # 2. BM25 sparse search
        try:
            bm25_results = self.bm25_store.search(clean_query, top_k=b_top_k)
        except Exception as exc:
            logger.error(f"BM25 sparse search failed: {exc}")
            bm25_results = []

        if not faiss_results and not bm25_results:
            logger.info("No candidates returned from dense or sparse search.")
            return []

        # 3. Reciprocal Rank Fusion
        fused_candidates = self.fusion.fuse(faiss_results, bm25_results)
        if not fused_candidates:
            return []

        # 4. Cross-Encoder reranking
        try:
            reranked = self.reranker.rerank(
                query=clean_query,
                candidates=fused_candidates,
                top_k=r_top_k,
            )
        except Exception as exc:
            logger.error(f"CrossEncoder reranking failed: {exc}")
            # Fall back to top fused candidates without reranking if reranker fails
            reranked = [
                (cand, cand.rrf_score)
                for cand in fused_candidates[:r_top_k]
            ]

        # 5. Build EvidenceChunk objects preserving provenance
        evidence_chunks: list[EvidenceChunk] = []
        for rank, (cand, rerank_score) in enumerate(reranked):
            chunk = cand.chunk
            meta = chunk.metadata

            evidence = EvidenceChunk(
                chunk_id=chunk.doc_id,
                doc_id=chunk.parent_doc_id or chunk.doc_id,
                content=chunk.content,
                source_label=f"[SOURCE_{rank + 1}]",
                source_name=meta.source_name,
                source_url=meta.source_url,
                title=chunk.title,
                authority=meta.authority,
                publication_date=meta.publication_date,
                document_type=meta.document_type,
                jurisdiction=meta.jurisdiction,
                faiss_score=cand.faiss_score,
                bm25_score=cand.bm25_score,
                rrf_score=cand.rrf_score,
                rerank_score=rerank_score,
                rank=rank,
            )
            evidence_chunks.append(evidence)

        logger.info(
            "Hybrid RAG search completed",
            extra={
                "query": clean_query[:50],
                "retrieved_evidence_count": len(evidence_chunks),
            },
        )
        return evidence_chunks
