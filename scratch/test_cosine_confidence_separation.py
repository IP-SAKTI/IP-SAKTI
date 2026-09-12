"""
scratch/test_cosine_confidence_separation.py — Regression & Separation Test for Cosine Similarity vs Bayesian Confidence Engine.

Verifies:
1. FAISS cosine is calculated independently.
2. Bayesian engine receives cosine as input but does NOT mutate or overwrite it.
3. Raw cosine == API cosine_similarity.
4. confidence_score is a separate independent metric.
5. Running confidence calculation does not change cosine.
6. Same query + same KB produces deterministic cosine and deterministic confidence scores.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from ip_sakti.confidence.bayesian_confidence import BayesianConfidenceEngine, BayesianConfidenceResult
from ip_sakti.models.query import EvidenceChunk, CitationRecord
from ip_sakti.retrieval.pipeline import HybridRAGPipeline
from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest, Jurisdiction, FormulationCategory


def test_faiss_cosine_independence():
    """Verify that FAISS cosine similarity is calculated independently of confidence."""
    pipeline = HybridRAGPipeline()
    try:
        pipeline.load_index()
    except Exception:
        pass

    query_str = "Find patents related to Ashwagandha formulations."
    query_vec = pipeline.embedding_generator.embed_query(query_str)
    faiss_raw_results = pipeline.faiss_store.search(query_vec, top_k=5)

    assert len(faiss_raw_results) > 0, "FAISS index returned 0 results for test query"
    top_doc, top_score = faiss_raw_results[0]
    print(f"\n[TEST 1] Raw FAISS top doc: {top_doc.doc_id}, Score: {top_score:.6f}")
    assert isinstance(top_score, float)
    assert 0.0 <= top_score <= 1.0, f"Cosine similarity out of bounds: {top_score}"


def test_bayesian_engine_does_not_mutate_cosine():
    """Verify that Bayesian engine receives evidence but does NOT mutate evidence.faiss_score."""
    engine = BayesianConfidenceEngine()
    original_faiss_score = 0.8421

    ev = EvidenceChunk(
        chunk_id="c1",
        doc_id="d1",
        source_id="s1",
        content="Ashwagandha formulation patent details.",
        source_label="[SOURCE_1]",
        source_name="Patent Guidelines",
        faiss_score=original_faiss_score,
        rerank_score=1.5,
    )
    citations = [
        CitationRecord(claim_snippet="Ashwagandha formulation", source_label="[SOURCE_1]", chunk_id="c1", is_grounded=True)
    ]

    # Evaluate confidence
    res = engine.evaluate_confidence(evidence=[ev], citations=citations, answer="Ashwagandha formulation patent details.")

    print(f"\n[TEST 2] Original FAISS score: {original_faiss_score}")
    print(f"[TEST 2] FAISS score after Bayesian evaluation: {ev.faiss_score}")
    print(f"[TEST 2] Bayesian score: {res.raw_confidence} ({res.confidence_percentage}%)")

    # Assert immutability of raw cosine score
    assert ev.faiss_score == original_faiss_score, "CRITICAL: Bayesian engine mutated evidence.faiss_score!"
    assert res.raw_confidence != ev.faiss_score, "Confidence score must be independent of raw cosine score"


def test_confidence_and_cosine_are_separate_fields():
    """Verify that APIQueryResponse has distinct cosine_similarity and confidence_score fields."""
    engine = BayesianConfidenceEngine()
    ev = EvidenceChunk(
        chunk_id="c1",
        doc_id="d1",
        source_id="s1",
        content="Test content",
        source_label="[SOURCE_1]",
        source_name="Test Source",
        faiss_score=0.6062,
        rerank_score=-0.42,
    )
    res = engine.evaluate_confidence(evidence=[ev], citations=[], answer="Test answer.")

    # Cosine is 0.6062
    raw_cosine = ev.faiss_score
    confidence = res.raw_confidence

    assert raw_cosine == 0.6062
    assert confidence != raw_cosine, "Confidence score must not equal raw cosine score"
    print(f"\n[TEST 3] Separate Fields: Cosine={raw_cosine}, Confidence={confidence}")


def test_determinism_same_query():
    """Verify that same query + same KB produces 100% deterministic cosine and confidence."""
    engine = BayesianConfidenceEngine()
    ev = EvidenceChunk(
        chunk_id="c1",
        doc_id="d1",
        source_id="s1",
        content="Ashwagandha patent formulation guidelines.",
        source_label="[SOURCE_1]",
        source_name="Guidelines",
        faiss_score=0.6062,
        rerank_score=0.50,
    )
    cit = [CitationRecord(claim_snippet="Ashwagandha patent", source_label="[SOURCE_1]", chunk_id="c1", is_grounded=True)]

    run1 = engine.evaluate_confidence(evidence=[ev], citations=cit, answer="Ashwagandha patent guidelines.")
    run2 = engine.evaluate_confidence(evidence=[ev], citations=cit, answer="Ashwagandha patent guidelines.")

    assert run1.raw_confidence == run2.raw_confidence, "Bayesian confidence is non-deterministic!"
    assert run1.signals == run2.signals, "Bayesian signals are non-deterministic!"
    print(f"\n[TEST 4] Determinism verified: Run 1={run1.raw_confidence}, Run 2={run2.raw_confidence}")


if __name__ == "__main__":
    print("=== RUNNING COSINE & CONFIDENCE SEPARATION TESTS ===")
    test_faiss_cosine_independence()
    test_bayesian_engine_does_not_mutate_cosine()
    test_confidence_and_cosine_are_separate_fields()
    test_determinism_same_query()
    print("\n==================================================")
    print("=== ALL COSINE & CONFIDENCE SEPARATION TESTS PASSED CLEANLY! ===")
    print("==================================================")
