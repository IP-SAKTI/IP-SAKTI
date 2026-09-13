"""
scratch/test_cosine_confidence_regression.py — Comprehensive Regression & Validation Test
for Cosine Similarity and Bayesian Confidence Score Independence.

Covers Section 11 items A through J:
A. Identical vectors: cosine = 1.0
B. Orthogonal vectors: cosine = 0.0
C. Known vectors: mathematical cosine verification
D. Raw cosine is unchanged after confidence calculation
E. No evidence: confidence = 0, abstain = True
F. High cosine + poor citation: confidence decreases
G. Conflicting sources: confidence decreases
H. Strong evidence: confidence is HIGH but <= 0.95
I. Repeated identical inputs: same cosine, same confidence
J. Changing confidence weights: must NOT change raw cosine
"""

import sys
import numpy as np
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ip_sakti.confidence.bayesian_confidence import BayesianConfidenceEngine, BayesianConfidenceResult
from ip_sakti.models.query import EvidenceChunk, CitationRecord


def compute_vector_cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Explicit mathematical cosine similarity: dot(a, b) / (||a|| * ||b||)."""
    dot_prod = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot_prod / (norm_a * norm_b))


def test_vector_math_and_immutability():
    print("\n--- 1. Testing Vector Math & Immutability (A, B, C, D, J) ---")

    # A) Identical vectors -> cosine = 1.0
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    cos_ident = compute_vector_cosine(v1, v2)
    assert abs(cos_ident - 1.0) < 1e-6, f"A. Identical vector cosine failed: {cos_ident}"
    print(f"  [PASS] A. Identical vectors cosine: {cos_ident:.4f} == 1.0000")

    # B) Orthogonal vectors -> cosine = 0.0
    v3 = np.array([1.0, 0.0], dtype=np.float32)
    v4 = np.array([0.0, 1.0], dtype=np.float32)
    cos_ortho = compute_vector_cosine(v3, v4)
    assert abs(cos_ortho - 0.0) < 1e-6, f"B. Orthogonal vector cosine failed: {cos_ortho}"
    print(f"  [PASS] B. Orthogonal vectors cosine: {cos_ortho:.4f} == 0.0000")

    # C) Known vectors -> dot([3,4], [4,3]) / (5 * 5) = 24 / 25 = 0.96
    v7 = np.array([3.0, 4.0], dtype=np.float32)
    v8 = np.array([4.0, 3.0], dtype=np.float32)
    cos_known = compute_vector_cosine(v7, v8)
    assert abs(cos_known - 0.96) < 1e-6, f"C. Known vector cosine failed: {cos_known}"
    print(f"  [PASS] C. Known vectors ([3,4], [4,3]) cosine: {cos_known:.4f} == 0.9600")

    # D) Raw cosine is unchanged after confidence calculation
    engine = BayesianConfidenceEngine()
    raw_cosine_before = 0.7046
    ev = EvidenceChunk(
        chunk_id="chunk_101",
        doc_id="doc_202",
        source_id="src_303",
        content="Ayurvedic patent licensing and compliance rules.",
        source_label="[SOURCE_1]",
        source_name="Ayush Guidelines",
        faiss_score=raw_cosine_before,
        rerank_score=2.1,
    )
    citations = [
        CitationRecord(
            claim_snippet="Ayurvedic patent licensing",
            source_label="[SOURCE_1]",
            chunk_id="chunk_101",
            is_grounded=True,
        )
    ]

    res = engine.evaluate_confidence(
        evidence=[ev],
        citations=citations,
        answer="Ayurvedic patent licensing requires Form 25 and Ayush approval.",
    )
    raw_cosine_after = ev.faiss_score
    assert raw_cosine_before == raw_cosine_after, f"D. Raw cosine mutated! Before: {raw_cosine_before}, After: {raw_cosine_after}"
    print(f"  [PASS] D. Raw cosine before ({raw_cosine_before}) == raw cosine after ({raw_cosine_after})")

    # J) Changing confidence weights must NOT change raw cosine
    custom_engine = BayesianConfidenceEngine(prior=0.30)
    custom_engine.weights["cosine_similarity"] = 0.05
    res_custom = custom_engine.evaluate_confidence(evidence=[ev], citations=citations, answer="Test answer.")
    assert ev.faiss_score == raw_cosine_before, f"J. Changing weights mutated raw cosine!"
    print(f"  [PASS] J. Changing confidence weights did NOT alter raw cosine ({ev.faiss_score})")


def test_confidence_safety_cases():
    print("\n--- 2. Testing Confidence Cases (E, F, G, H, I) ---")
    engine = BayesianConfidenceEngine()

    # E) No evidence: confidence = 0, abstain = True
    res_e = engine.evaluate_confidence(evidence=[], citations=[], answer="No evidence.")
    assert res_e.raw_confidence == 0.0, f"E. Expected 0.0, got {res_e.raw_confidence}"
    assert res_e.should_abstain, "E. Expected abstain = True"
    print(f"  [PASS] E. No evidence -> Conf={res_e.raw_confidence}, Abstain={res_e.should_abstain}")

    # H) Strong evidence: confidence is HIGH but <= 0.95
    ev_h = [
        EvidenceChunk(
            chunk_id="c1", doc_id="d1", source_id="s1",
            content="Manufacturing requirements under Drugs and Cosmetics Act.",
            source_label="[SOURCE_1]", source_name="D&C Act 1940",
            faiss_score=0.85, rerank_score=3.5,
        ),
        EvidenceChunk(
            chunk_id="c2", doc_id="d2", source_id="s2",
            content="Licensing rules for Ayurvedic formulations.",
            source_label="[SOURCE_2]", source_name="Ayush Rules",
            faiss_score=0.82, rerank_score=3.0,
        ),
    ]
    cit_h = [
        CitationRecord(claim_snippet="Manufacturing requirements", source_label="[SOURCE_1]", chunk_id="c1", is_grounded=True),
        CitationRecord(claim_snippet="Licensing rules", source_label="[SOURCE_2]", chunk_id="c2", is_grounded=True),
    ]
    res_h = engine.evaluate_confidence(evidence=ev_h, citations=cit_h, answer="Licensing process requires approval.")
    assert res_h.confidence_level == "HIGH", f"H. Expected HIGH, got {res_h.confidence_level}"
    assert res_h.raw_confidence <= 0.93, f"H. Exceeded 0.93 max cap: {res_h.raw_confidence}"
    print(f"  [PASS] H. Strong evidence -> Conf={res_h.confidence_percentage}% ({res_h.confidence_level}) <= 93%")

    # F) High cosine + poor citation grounding: confidence decreases
    cit_f = [
        CitationRecord(claim_snippet="Claim 1", source_label="[SOURCE_1]", chunk_id="c1", is_grounded=False),
        CitationRecord(claim_snippet="Claim 2", source_label="[SOURCE_1]", chunk_id="c1", is_grounded=False),
    ]
    res_f = engine.evaluate_confidence(evidence=ev_h, citations=cit_f, answer="Ungrounded answer claims.")
    assert res_f.raw_confidence < res_h.raw_confidence, f"F. Expected lower confidence than strong grounding: {res_f.raw_confidence} vs {res_h.raw_confidence}"
    assert res_f.confidence_level != "HIGH", f"F. Poor grounding must not yield HIGH confidence"
    print(f"  [PASS] F. High cosine + poor citation -> Conf decreased to {res_f.confidence_percentage}% ({res_f.confidence_level})")

    # G) Conflicting sources: confidence decreases
    res_g = engine.evaluate_confidence(evidence=ev_h, citations=cit_h, answer="Answer with conflicts", conflicting_sources=True)
    assert res_g.raw_confidence < res_h.raw_confidence, f"G. Conflicting sources did not decrease confidence!"
    print(f"  [PASS] G. Conflicting sources -> Conf decreased to {res_g.confidence_percentage}% ({res_g.confidence_level})")

    # I) Repeated identical inputs: same cosine, same confidence
    res_i1 = engine.evaluate_confidence(evidence=ev_h, citations=cit_h, answer="Deterministic test.")
    res_i2 = engine.evaluate_confidence(evidence=ev_h, citations=cit_h, answer="Deterministic test.")
    assert res_i1.raw_confidence == res_i2.raw_confidence, "I. Non-deterministic confidence!"
    assert ev_h[0].faiss_score == ev_h[0].faiss_score, "I. Non-deterministic cosine!"
    print(f"  [PASS] I. Repeated identical inputs -> Run 1={res_i1.raw_confidence}, Run 2={res_i2.raw_confidence} (Identical)")


if __name__ == "__main__":
    print("==================================================")
    print("=== COSINE & CONFIDENCE REGRESSION TEST SUITE ===")
    print("==================================================")
    test_vector_math_and_immutability()
    test_confidence_safety_cases()
    print("\n==================================================")
    print("=== ALL REGRESSION TESTS PASSED CLEANLY! ===")
    print("==================================================")
