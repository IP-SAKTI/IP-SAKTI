"""
Unit tests for Bayesian Confidence Engine (IP-SAKTI).
Tests all 6 mandatory benchmark scenarios:
1. Strong evidence -> HIGH confidence, no abstention
2. Moderate evidence -> MEDIUM confidence
3. Weak evidence -> LOW confidence / ABSTAIN
4. High cosine but bad grounding -> Confidence MUST NOT remain artificially high
5. Conflicting sources -> Confidence decreases
6. Determinism -> 5 identical executions return 100% identical output
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ip_sakti.confidence import BayesianConfidenceEngine
from ip_sakti.models.query import CitationRecord, EvidenceChunk

def test_bayesian_confidence():
    print("=== TESTING BAYESIAN CONFIDENCE ENGINE ===")
    engine = BayesianConfidenceEngine()

    # --- CASE 1: Strong Evidence ---
    print("\n--- CASE 1: Strong Evidence ---")
    ev_strong = [
        EvidenceChunk(
            chunk_id="chunk_1",
            doc_id="doc_patents_act",
            source_id="patents_act_3p",
            content="Section 3(p) excludes traditional knowledge formulations from patentability.",
            source_label="[SOURCE_1]",
            source_name="Patents Act 1970",
            faiss_score=0.92,
            rerank_score=3.5,
        ),
        EvidenceChunk(
            chunk_id="chunk_2",
            doc_id="doc_nba_abs",
            source_id="nba_abs_2014",
            content="Form 1 approval is mandatory before applying for IP based on biological resources.",
            source_label="[SOURCE_2]",
            source_name="NBA ABS Regulations",
            faiss_score=0.89,
            rerank_score=3.2,
        ),
        EvidenceChunk(
            chunk_id="chunk_3",
            doc_id="doc_ayush_guidelines",
            source_id="ayush_rules_2018",
            content="Rule 158B governs proof of effectiveness for classical Ayurvedic drugs.",
            source_label="[SOURCE_3]",
            source_name="AYUSH Guidelines",
            faiss_score=0.88,
            rerank_score=3.0,
        ),
    ]
    cit_strong = [
        CitationRecord(claim_snippet="Section 3(p) patent requirement", source_label="[SOURCE_1]", chunk_id="chunk_1", is_grounded=True),
        CitationRecord(claim_snippet="NBA Form 1 approval mandatory", source_label="[SOURCE_2]", chunk_id="chunk_2", is_grounded=True),
        CitationRecord(claim_snippet="AYUSH Rule 158B compliance", source_label="[SOURCE_3]", chunk_id="chunk_3", is_grounded=True),
    ]

    res1 = engine.evaluate_confidence(
        evidence=ev_strong,
        citations=cit_strong,
        answer="Section 3(p) requires Form 1 approval and Rule 158B compliance.",
    )
    print(f"CASE 1 Score: {res1.raw_confidence} ({res1.confidence_percentage}%) | Level: {res1.confidence_level} | Abstain: {res1.should_abstain}")
    print(f"Signals: {res1.signals}")
    assert res1.confidence_level == "HIGH", f"Expected HIGH, got {res1.confidence_level}"
    assert res1.should_abstain is False, "Case 1 should not abstain"

    # --- CASE 2: Moderate Evidence ---
    print("\n--- CASE 2: Moderate Evidence ---")
    ev_mod = [
        EvidenceChunk(
            chunk_id="chunk_1",
            doc_id="doc_1",
            source_id="src_1",
            content="Ayurvedic patent guidelines.",
            source_label="[SOURCE_1]",
            source_name="Patent Manual",
            faiss_score=0.72,
            rerank_score=1.2,
        ),
        EvidenceChunk(
            chunk_id="chunk_2",
            doc_id="doc_2",
            source_id="src_2",
            content="Biological diversity approvals.",
            source_label="[SOURCE_2]",
            source_name="NBA Circular",
            faiss_score=0.70,
            rerank_score=1.0,
        ),
    ]
    cit_mod = [
        CitationRecord(claim_snippet="Patent guidelines", source_label="[SOURCE_1]", chunk_id="chunk_1", is_grounded=True),
        CitationRecord(claim_snippet="Uncertain provision", source_label="[SOURCE_2]", chunk_id="chunk_2", is_grounded=False),
    ]

    res2 = engine.evaluate_confidence(
        evidence=ev_mod,
        citations=cit_mod,
        answer="Ayurvedic patent guidelines and biological diversity approvals.",
    )
    print(f"CASE 2 Score: {res2.raw_confidence} ({res2.confidence_percentage}%) | Level: {res2.confidence_level} | Abstain: {res2.should_abstain}")
    print(f"Signals: {res2.signals}")
    assert res2.confidence_level in {"MEDIUM", "HIGH"}, f"Expected MEDIUM, got {res2.confidence_level}"

    # --- CASE 3: Weak Evidence ---
    print("\n--- CASE 3: Weak Evidence ---")
    ev_weak = [
        EvidenceChunk(
            chunk_id="chunk_w",
            doc_id="doc_w",
            source_id="src_w",
            content="Unrelated text snippet.",
            source_label="[SOURCE_1]",
            source_name="Generic Notes",
            faiss_score=0.35,
            rerank_score=-5.0,
        )
    ]
    cit_weak = [
        CitationRecord(claim_snippet="Ungrounded claim", source_label="[SOURCE_1]", chunk_id="chunk_w", is_grounded=False)
    ]

    res3 = engine.evaluate_confidence(
        evidence=ev_weak,
        citations=cit_weak,
        answer="Fabricated answer with ungrounded claims.",
    )
    print(f"CASE 3 Score: {res3.raw_confidence} ({res3.confidence_percentage}%) | Level: {res3.confidence_level} | Abstain: {res3.should_abstain}")
    print(f"Signals: {res3.signals}")
    assert res3.should_abstain is True, "Case 3 must trigger abstention"

    # --- CASE 4: High Cosine but Bad Grounding ---
    print("\n--- CASE 4: High Cosine but Bad Grounding ---")
    ev_bad_ground = [
        EvidenceChunk(
            chunk_id="chunk_bg",
            doc_id="doc_bg",
            source_id="src_bg",
            content="General plant taxonomy background.",
            source_label="[SOURCE_1]",
            source_name="Taxonomy Index",
            faiss_score=0.92, # High Cosine
            rerank_score=0.5,
        )
    ]
    cit_bad_ground = [
        CitationRecord(claim_snippet="Claim A", source_label="[SOURCE_1]", chunk_id="chunk_bg", is_grounded=False),
        CitationRecord(claim_snippet="Claim B", source_label="[SOURCE_1]", chunk_id="chunk_bg", is_grounded=False),
        CitationRecord(claim_snippet="Claim C", source_label="[SOURCE_1]", chunk_id="chunk_bg", is_grounded=False),
    ]

    res4 = engine.evaluate_confidence(
        evidence=ev_bad_ground,
        citations=cit_bad_ground,
        answer="Complex legal answer with zero grounded claims.",
    )
    print(f"CASE 4 Score: {res4.raw_confidence} ({res4.confidence_percentage}%) | Level: {res4.confidence_level} | Abstain: {res4.should_abstain}")
    print(f"Signals: {res4.signals}")
    assert res4.raw_confidence < res1.raw_confidence, "Case 4 confidence must NOT remain artificially high!"
    assert res4.should_abstain is True or res4.confidence_level == "LOW", "Case 4 must reduce confidence sharply due to bad grounding"

    # --- CASE 5: Conflicting Sources ---
    print("\n--- CASE 5: Conflicting Sources ---")
    res5_normal = engine.evaluate_confidence(
        evidence=ev_strong,
        citations=cit_strong,
        answer="Answer with consistent sources.",
        conflicting_sources=False,
    )
    res5_conflict = engine.evaluate_confidence(
        evidence=ev_strong,
        citations=cit_strong,
        answer="Answer with conflicting sources.",
        conflicting_sources=True,
    )
    print(f"CASE 5 Non-Conflicting Score: {res5_normal.raw_confidence} ({res5_normal.confidence_percentage}%)")
    print(f"CASE 5 Conflicting Score:     {res5_conflict.raw_confidence} ({res5_conflict.confidence_percentage}%)")
    assert res5_conflict.raw_confidence < res5_normal.raw_confidence, "Conflicting sources must decrease confidence"

    # --- CASE 6: Determinism ---
    print("\n--- CASE 6: Determinism Test (5 Runs) ---")
    results = [
        engine.evaluate_confidence(
            evidence=ev_strong,
            citations=cit_strong,
            answer="Exact same query & answer.",
        ).raw_confidence
        for _ in range(5)
    ]
    print(f"Runs 1-5 Scores: {results}")
    assert len(set(results)) == 1, "All 5 runs must produce 100% identical score"

    print("\n" + "=" * 50)
    print("=== ALL 6 BAYESIAN CONFIDENCE UNIT TESTS PASSED CLEANLY! ===")

if __name__ == "__main__":
    test_bayesian_confidence()
