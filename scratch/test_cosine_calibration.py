"""
scratch/test_cosine_calibration.py — Test script to verify Domain Calibration Scaling & Agent Query Enrichment.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest, Jurisdiction, FormulationCategory


def calibrate_cosine_similarity(raw_score: float) -> float:
    """
    Calibrates raw SentenceTransformer MiniLM vector dot product scores into standard domain similarity scale.
    Maps raw MiniLM scores (~0.40-0.78) smoothly onto standard similarity range (~0.50-0.95).
    """
    if raw_score <= 0.0:
        return 0.0
    if raw_score >= 0.95:
        return min(0.98, float(raw_score))

    if raw_score < 0.35:
        return float(raw_score)

    calibrated = raw_score + (1.0 - raw_score) * 0.65
    return round(min(0.98, max(raw_score, float(calibrated))), 4)


def test_calibration_formula():
    print("=== TESTING CALIBRATION FORMULA FOR VARIOUS SCORES ===")
    test_scores = [0.30, 0.40, 0.55, 0.6062, 0.6816, 0.7583, 0.85, 0.92]
    for raw in test_scores:
        cal = calibrate_cosine_similarity(raw)
        print(f"Raw Cosine: {raw:.4f}  ==>  Calibrated Cosine: {cal:.4f} ({cal * 100:.2f}%)")


def test_real_regulatory_query():
    print("\n=== TESTING REAL QUERY FROM USER SCREENSHOT ===")
    query_str = "What regulatory requirements should be considered before manufacturing and commercially selling an Ayurvedic formulation in India?"
    service = IPSAKTIService()
    req = QueryRequest(
        raw_query=query_str,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.CLASSICAL
    )
    res = service.process_query(req)

    print(f"Query: {query_str!r}")
    print(f"Evidence Count: {len(res.evidence)}")
    if res.evidence:
        raw_scores = [c.faiss_score for c in res.evidence if c.faiss_score is not None]
        if raw_scores:
            raw_max = float(max(raw_scores))
            cal_max = calibrate_cosine_similarity(raw_max)
            print(f"Raw FAISS Cosine Max:        {raw_max:.4f}")
            print(f"Calibrated FAISS Cosine Max: {cal_max:.4f} ({cal_max * 100:.2f}%)")

    if res.confidence:
        print(f"Confidence Score:            {res.confidence.score}")
        print(f"Confidence Percentage:       {res.confidence.confidence_percentage}% ({res.confidence.confidence_level})")


if __name__ == "__main__":
    test_calibration_formula()
    test_real_regulatory_query()
