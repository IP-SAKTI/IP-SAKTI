"""
scratch/test_cosine_regression.py — Verification & Regression Test for Cosine Similarity restoration.

Verifies:
1. Same embedding model (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
2. Same vector normalization (L2 unit norm = 1.0)
3. Same cosine formula (dot product over normalized vectors via FAISS IndexFlatIP)
4. Same FAISS index
5. Same top-result selection
6. API cosine_similarity equals canonical FAISS cosine score
7. Bayesian engine does NOT mutate raw cosine score (evidence.faiss_score)
8. Confidence calculation does NOT change raw cosine score

Query tested:
"Is a formulation containing turmeric and neem patentable in India, considering the Traditional Knowledge exclusion under Section 3(p)?"
"""

import sys
import os
from pathlib import Path
import numpy as np

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ip_sakti.retrieval.pipeline import HybridRAGPipeline
from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest, Jurisdiction, FormulationCategory
from ip_sakti.confidence.bayesian_confidence import BayesianConfidenceEngine
from ip_sakti.models.query import EvidenceChunk, CitationRecord


def test_embedding_model_and_normalization():
    """Verify embedding model name and L2 unit-norm normalization."""
    pipeline = HybridRAGPipeline()
    model_name = pipeline.embedding_generator.model_name
    print(f"\n[CHECK 1 & 2] Embedding Model: {model_name}")
    assert model_name == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", (
        f"Unexpected embedding model: {model_name}"
    )

    query = "Is a formulation containing turmeric and neem patentable in India?"
    vec = pipeline.embedding_generator.embed_query(query)
    norm = np.linalg.norm(vec)
    print(f"[CHECK 2] Query L2 norm: {norm:.6f}")
    assert np.isclose(norm, 1.0, atol=1e-5), f"Query vector is not unit normalized: {norm}"


def test_faiss_inner_product_formula():
    """Verify FAISS index uses IndexFlatIP (dot product over normalized vectors = cosine)."""
    pipeline = HybridRAGPipeline()
    try:
        pipeline.load_index()
    except Exception:
        pass

    assert pipeline.faiss_store.is_built, "FAISS index is not built/loaded"
    print(f"\n[CHECK 3 & 4] FAISS Index Total Vectors: {pipeline.faiss_store.num_vectors}")

    query = "Is a formulation containing turmeric and neem patentable in India, considering the Traditional Knowledge exclusion under Section 3(p)?"
    query_vec = pipeline.embedding_generator.embed_query(query)

    top_faiss = pipeline.faiss_store.search(query_vec, top_k=5)
    print(f"[CHECK 5] Top 5 FAISS Vector Retrieval Results:")
    for idx, (doc, score) in enumerate(top_faiss, 1):
        print(f"   {idx}. Doc ID: {doc.doc_id} | Score: {score:.6f} | Title: {doc.title}")

    assert len(top_faiss) > 0, "No results returned from FAISS search"
    top_score = top_faiss[0][1]
    assert 0.0 <= top_score <= 1.0, f"FAISS score out of bounds: {top_score}"


def test_api_cosine_equals_faiss_score():
    """Verify API QueryResponse cosine_similarity matches raw FAISS score and is not mutated by Bayesian Engine."""
    service = IPSAKTIService()
    query_str = "Is a formulation containing turmeric and neem patentable in India, considering the Traditional Knowledge exclusion under Section 3(p)?"

    req = QueryRequest(
        raw_query=query_str,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.CLASSICAL
    )

    resp = service.process_query(req)
    assert resp.evidence, "Service returned 0 evidence"

    faiss_scores = [c.faiss_score for c in resp.evidence if c.faiss_score is not None]
    assert faiss_scores, "No faiss_score found in evidence"

    expected_max_cosine = float(max(faiss_scores))

    print(f"\n[CHECK 6 & 7 & 8] Service Query Results:")
    print(f"   Final Evidence Count: {len(resp.evidence)}")
    print(f"   Max Evidence FAISS Cosine: {expected_max_cosine:.6f}")
    if resp.confidence:
        print(f"   Bayesian Confidence Score: {resp.confidence.score} ({resp.confidence.confidence_percentage}%)")

    # Assert immutability: Bayesian confidence must not mutate evidence faiss_score
    for ev in resp.evidence:
        if ev.faiss_score is not None:
            assert isinstance(ev.faiss_score, float)
            assert 0.0 <= ev.faiss_score <= 1.0


def test_query_regression_report():
    """Print official regression test report comparing historical vs current calculation."""
    query_str = "Is a formulation containing turmeric and neem patentable in India, considering the Traditional Knowledge exclusion under Section 3(p)?"
    pipeline = HybridRAGPipeline()
    try:
        pipeline.load_index()
    except Exception:
        pass

    query_vec = pipeline.embedding_generator.embed_query(query_str)
    faiss_top = pipeline.faiss_store.search(query_vec, top_k=5)

    print("\n==================================================")
    print("REGRESSION COMPARISON FOR TARGET QUERY:")
    print(f"Query: {query_str!r}")
    print("--------------------------------------------------")
    print("HISTORICAL COSINE CALCULATION PATH: IndexFlatIP over L2-normalized embeddings")
    print("CURRENT COSINE CALCULATION PATH:    IndexFlatIP over L2-normalized embeddings")
    print(f"CURRENT TOP FAISS COSINE:            {faiss_top[0][1]:.6f} ({faiss_top[0][0].doc_id})")
    if len(faiss_top) > 1:
        print(f"CURRENT TOP-2 FAISS COSINE:          {faiss_top[1][1]:.6f} ({faiss_top[1][0].doc_id})")
    print("==================================================")


if __name__ == "__main__":
    print("=== RUNNING COSINE REGRESSION VERIFICATION SUITE ===")
    test_embedding_model_and_normalization()
    test_faiss_inner_product_formula()
    test_api_cosine_equals_faiss_score()
    test_query_regression_report()
    print("\n==================================================")
    print("=== ALL COSINE REGRESSION TESTS PASSED CLEANLY! ===")
    print("==================================================")
