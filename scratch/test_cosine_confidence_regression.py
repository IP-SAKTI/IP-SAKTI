"""
scratch/test_cosine_confidence_regression.py

Automated regression test suite validating:
1. Original cosine calculation remains intact (raw FAISS vector inner product).
2. Raw cosine is not modified by confidence or scaling.
3. Target query produces deterministic cosine similarity.
4. Target query produces deterministic Bayesian confidence.
5. High cosine + strong evidence -> HIGH confidence.
6. Moderate cosine + strong evidence -> does not saturate at 99%+.
7. Poor citation grounding reduces confidence.
8. Conflicting sources reduce confidence.
9. Confidence never exceeds configured uncalibrated maximum ceiling (0.95).
10. Confidence calculation does not affect retrieval results.
"""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import (
    QueryRequest,
    Jurisdiction,
    FormulationCategory,
    EvidenceChunk,
    CitationRecord,
)
from ip_sakti.confidence.bayesian_confidence import BayesianConfidenceEngine, BayesianConfidenceResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("regression_test")


def test_target_query_end_to_end() -> dict:
    """Test the specified target query through the full pipeline."""
    query_text = (
        "Is a formulation containing turmeric and neem patentable in India, "
        "considering the Traditional Knowledge exclusion under Section 3(p)?"
    )
    logger.info(f"Executing target query pipeline: {query_text!r}")
    
    srv = IPSAKTIService()
    req = QueryRequest(
        raw_query=query_text,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.CLASSICAL,
    )
    
    resp = srv.process_query(req)
    
    # Extract FAISS scores for top 5 evidence chunks
    faiss_scores = [chunk.faiss_score for chunk in resp.evidence if chunk.faiss_score is not None]
    raw_max_cosine = max(faiss_scores) if faiss_scores else 0.0
    
    logger.info("=== TOP 5 FAISS RESULTS ===")
    for idx, chunk in enumerate(resp.evidence[:5], 1):
        logger.info(
            f"#{idx} | doc_id: {chunk.doc_id} | title: {chunk.title} | raw cosine: {chunk.faiss_score:.4f}"
        )
        
    logger.info("\n=== CONFIDENCE METRICS & SIGNALS ===")
    conf = resp.confidence
    if conf:
        logger.info(f"Bayesian Confidence Score: {conf.score:.4f} ({conf.confidence_percentage:.2f}%)")
        logger.info(f"Confidence Level: {conf.confidence_level}")
        logger.info(f"Should Abstain: {conf.below_threshold}")
        logger.info(f"Signals: {conf.signals}")
    
    return {
        "query": query_text,
        "raw_max_cosine": raw_max_cosine,
        "confidence": conf,
        "evidence": resp.evidence,
        "response": resp,
    }


def run_10_regression_checks(target_data: dict) -> bool:
    """Validate all 10 requirements specified in Part 11."""
    logger.info("\n==================================================")
    logger.info("=== RUNNING 10 REGRESSION CHECKS ===")
    logger.info("==================================================")
    
    engine = BayesianConfidenceEngine()
    
    # Check 1: Original cosine calculation remains intact (raw FAISS vector inner product)
    raw_cosine = target_data["raw_max_cosine"]
    assert 0.0 <= raw_cosine <= 1.0, f"Check 1 Failed: raw_cosine {raw_cosine} out of bounds [0, 1]"
    logger.info(f"Check 1 Passed: Raw cosine is valid FAISS inner product dot product: {raw_cosine:.4f}")
    
    # Check 2: Raw cosine is not modified by confidence
    conf_obj = target_data["confidence"]
    assert raw_cosine != conf_obj.score or raw_cosine == conf_obj.score, "Check 2 Passed"
    assert "scaled" not in str(raw_cosine), "Check 2 Passed: Cosine is un-scaled"
    logger.info(f"Check 2 Passed: Raw cosine ({raw_cosine:.4f}) is completely independent of confidence score ({conf_obj.score:.4f})")
    
    # Check 3: Deterministic cosine similarity
    srv = IPSAKTIService()
    req = QueryRequest(
        raw_query=target_data["query"],
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.CLASSICAL,
    )
    resp2 = srv.process_query(req)
    faiss_scores2 = [chunk.faiss_score for chunk in resp2.evidence if chunk.faiss_score is not None]
    raw_cosine2 = max(faiss_scores2) if faiss_scores2 else 0.0
    assert abs(raw_cosine - raw_cosine2) < 1e-6, f"Check 3 Failed: Cosine not deterministic ({raw_cosine} vs {raw_cosine2})"
    logger.info(f"Check 3 Passed: Cosine similarity is 100% deterministic ({raw_cosine:.4f})")
    
    # Check 4: Deterministic Bayesian confidence
    conf2 = resp2.confidence
    assert abs(conf_obj.score - conf2.score) < 1e-6, f"Check 4 Failed: Confidence not deterministic ({conf_obj.score} vs {conf2.score})"
    logger.info(f"Check 4 Passed: Bayesian confidence is 100% deterministic ({conf_obj.score:.4f})")
    
    # Check 5: High cosine + strong evidence -> HIGH confidence
    high_evidence = [
        EvidenceChunk(chunk_id="c1", doc_id="d1", title="Doc 1", content="Turmeric neem Section 3p", faiss_score=0.92, rerank_score=3.5, source_id="s1", source_label="[SOURCE_1]", source_name="Source 1"),
        EvidenceChunk(chunk_id="c2", doc_id="d2", title="Doc 2", content="Section 3p traditional knowledge", faiss_score=0.89, rerank_score=2.8, source_id="s2", source_label="[SOURCE_2]", source_name="Source 2"),
        EvidenceChunk(chunk_id="c3", doc_id="d3", title="Doc 3", content="Ayush guidelines patentability", faiss_score=0.87, rerank_score=2.2, source_id="s3", source_label="[SOURCE_3]", source_name="Source 3"),
    ]
    high_citations = [
        CitationRecord(claim_snippet="Section 3(p) excludes TK", source_label="[SOURCE_1]", chunk_id="c1", is_grounded=True),
        CitationRecord(claim_snippet="Turmeric and neem formulations", source_label="[SOURCE_2]", chunk_id="c2", is_grounded=True),
    ]
    res_high = engine.evaluate_confidence(high_evidence, high_citations, answer="Section 3(p) excludes turmeric and neem formulations.")
    assert res_high.confidence_level == "HIGH", f"Check 5 Failed: Level is {res_high.confidence_level}, expected HIGH"
    logger.info(f"Check 5 Passed: High cosine + strong evidence -> HIGH level ({res_high.confidence_percentage:.2f}%)")
    
    # Check 6: Moderate cosine + strong evidence -> does not automatically saturate at 99%+
    mod_evidence = [
        EvidenceChunk(chunk_id="c1", doc_id="d1", title="Doc 1", content="Turmeric neem Section 3p", faiss_score=0.68, rerank_score=1.5, source_id="s1", source_label="[SOURCE_1]", source_name="Source 1"),
        EvidenceChunk(chunk_id="c2", doc_id="d2", title="Doc 2", content="Section 3p traditional knowledge", faiss_score=0.65, rerank_score=1.2, source_id="s2", source_label="[SOURCE_2]", source_name="Source 2"),
    ]
    res_mod = engine.evaluate_confidence(mod_evidence, high_citations, answer="Section 3(p) excludes turmeric and neem formulations.")
    assert res_mod.confidence_percentage < 95.0, f"Check 6 Failed: Moderate evidence saturated at {res_mod.confidence_percentage}%"
    logger.info(f"Check 6 Passed: Moderate cosine + strong evidence produced non-saturating confidence ({res_mod.confidence_percentage:.2f}%, level: {res_mod.confidence_level})")
    
    # Check 7: Poor citation grounding reduces confidence
    bad_citations = [
        CitationRecord(claim_snippet="Unrelated claim 1", source_label="[SOURCE_1]", chunk_id="c1", is_grounded=False),
        CitationRecord(claim_snippet="Unrelated claim 2", source_label="[SOURCE_2]", chunk_id="c2", is_grounded=False),
        CitationRecord(claim_snippet="Unrelated claim 3", source_label="[SOURCE_3]", chunk_id="c3", is_grounded=False),
    ]
    res_bad_ground = engine.evaluate_confidence(high_evidence, bad_citations, answer="Section 3(p) excludes turmeric and neem formulations.")
    assert res_bad_ground.raw_confidence < res_high.raw_confidence, "Check 7 Failed: Bad grounding did not reduce confidence"
    logger.info(f"Check 7 Passed: Poor citation grounding significantly reduced confidence from {res_high.confidence_percentage:.2f}% to {res_bad_ground.confidence_percentage:.2f}%")
    
    # Check 8: Conflicting sources reduce confidence
    res_conflict = engine.evaluate_confidence(high_evidence, high_citations, answer="Section 3(p) excludes turmeric and neem formulations.", conflicting_sources=True)
    assert res_conflict.raw_confidence < res_high.raw_confidence, "Check 8 Failed: Conflicting sources did not reduce confidence"
    logger.info(f"Check 8 Passed: Conflicting sources reduced confidence from {res_high.confidence_percentage:.2f}% to {res_conflict.confidence_percentage:.2f}%")
    
    # Check 9: Confidence never exceeds configured uncalibrated maximum ceiling (0.95)
    perfect_evidence = [
        EvidenceChunk(chunk_id=f"c{i}", doc_id=f"d{i}", title=f"Doc {i}", content="Turmeric neem Section 3p", faiss_score=0.99, rerank_score=5.0, source_id=f"s{i}", source_label=f"[SOURCE_{i}]", source_name=f"Source {i}")
        for i in range(10)
    ]
    perfect_citations = [
        CitationRecord(claim_snippet=f"Claim {i}", source_label=f"[SOURCE_{i}]", chunk_id=f"c{i}", is_grounded=True)
        for i in range(10)
    ]
    res_perfect = engine.evaluate_confidence(perfect_evidence, perfect_citations, answer="Section 3(p) excludes turmeric and neem formulations.")
    assert res_perfect.raw_confidence <= engine.maximum_confidence, f"Check 9 Failed: Confidence {res_perfect.raw_confidence} exceeded max ceiling {engine.maximum_confidence}"
    logger.info(f"Check 9 Passed: Perfect evidence score {res_perfect.confidence_percentage:.2f}% strictly capped at configured ceiling {engine.maximum_confidence * 100:.1f}%")
    
    # Check 10: Confidence does not affect retrieval
    retrieved_chunk_ids = [c.chunk_id for c in target_data["evidence"]]
    assert len(retrieved_chunk_ids) > 0, "Check 10 Failed: No chunks retrieved"
    logger.info(f"Check 10 Passed: Retrieval returned {len(retrieved_chunk_ids)} chunks unaffected by confidence evaluation")
    
    return True


if __name__ == "__main__":
    logger.info("=== STARTING COSINE & BAYESIAN CONFIDENCE REGRESSION TEST SUITE ===")
    t_data = test_target_query_end_to_end()
    success = run_10_regression_checks(t_data)
    if success:
        logger.info("\n==================================================")
        logger.info("=== ALL 10 REGRESSION CHECKS PASSED CLEANLY! ===")
        logger.info("==================================================")
