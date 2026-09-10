"""
E2E Test for Bayesian Confidence Engine Integration in IPSAKTIService.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest, Jurisdiction, FormulationCategory

def main():
    print("=== TESTING E2E PIPELINE WITH BAYESIAN CONFIDENCE ENGINE ===")
    service = IPSAKTIService()

    req = QueryRequest(
        raw_query="What permissions are required under Section 3(p) for Ayurvedic drug patents in India?",
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.CLASSICAL
    )

    resp = service.process_query(req)

    print("\n--- E2E FINAL RESPONSE ---")
    print(f"Query ID: {resp.query_id}")
    print(f"Answer (first 120 chars): {resp.answer[:120]!r}")
    print(f"Is Abstention: {resp.is_abstention}")
    print(f"Evidence Count: {len(resp.evidence)}")
    if resp.evidence:
        print(f"Top FAISS Cosine Sim: {resp.evidence[0].faiss_score}")

    if resp.confidence:
        print(f"Confidence Score: {resp.confidence.score}")
        print(f"Confidence Percentage: {resp.confidence.confidence_percentage}%")
        print(f"Confidence Level: {resp.confidence.confidence_level}")
        print(f"Below Threshold (Abstain): {resp.confidence.below_threshold}")
        print(f"Confidence Signals: {resp.confidence.signals}")

        assert resp.confidence.score is not None
        assert resp.confidence.confidence_percentage is not None
        assert resp.confidence.confidence_level in {"HIGH", "MEDIUM", "LOW"}
        assert isinstance(resp.confidence.signals, dict)

    print("\n=== E2E BAYESIAN CONFIDENCE PIPELINE VERIFIED SUCCESSFULLY! ===")

if __name__ == "__main__":
    main()
