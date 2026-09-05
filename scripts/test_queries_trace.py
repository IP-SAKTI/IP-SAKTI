"""
scripts/test_queries_trace.py — End-to-End Query Tracing Diagnostic (Phase 2, 6, 11).

Traces the execution of test queries through PipelineCoordinator, showing:
- Detected language & confidence
- Normalized & translated query
- Classification & jurisdiction
- Selected agent
- Top retrieved evidence chunks with BM25, FAISS, RRF & Cross-Encoder scores
- Citation validation records
- Calculated confidence score & abstention status
- Final generated answer
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ip_sakti.models.query import FormulationCategory, Jurisdiction, QueryRequest
from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.service import IPSAKTIService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def trace_query(service: IPSAKTIService, query_text: str, label: str):
    print("\n" + "=" * 80)
    print(f"QUERY TRACE: {label}")
    print(f"Raw Input: '{query_text}'")
    print("=" * 80)

    request = QueryRequest(
        raw_query=query_text,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.PROPRIETARY,
    )

    response = service.process_query(request)

    print(f"Is Abstention:   {response.is_abstention}")
    if response.confidence:
        print(f"Confidence Score:{response.confidence.score:.4f} (Below threshold: {response.confidence.below_threshold})")
        print(f"Confidence Reason:{response.confidence.reason}")
    print(f"Agents Invoked:  {[a.value for a in response.agents_invoked]}")
    print(f"Evidence Count:  {len(response.evidence)}")

    print("\n--- TOP RETRIEVED EVIDENCE CHUNKS ---")
    for idx, chunk in enumerate(response.evidence, start=1):
        print(f"[{idx}] {chunk.source_label} - Title: {chunk.title}")
        print(f"    URL: {chunk.source_url}")
        f_score = f"{chunk.faiss_score:.4f}" if chunk.faiss_score is not None else "N/A"
        b_score = f"{chunk.bm25_score:.2f}" if chunk.bm25_score is not None else "N/A"
        r_score = f"{chunk.rrf_score:.4f}" if chunk.rrf_score is not None else "N/A"
        re_score = f"{chunk.rerank_score:.4f}" if chunk.rerank_score is not None else "N/A"
        print(f"    Scores -> FAISS: {f_score}, BM25: {b_score}, RRF: {r_score}, Rerank: {re_score}")
        print(f"    Preview: {chunk.content[:120]}...")

    print("\n--- CITATION VALIDATION ---")
    print(f"Total Citations: {len(response.citations)}")
    for cit in response.citations:
        print(f"    Claim: '{cit.claim_snippet}' -> Label: {cit.source_label}, Grounded: {cit.is_grounded}")

    print("\n--- FINAL ANSWER ---")
    print(response.answer)
    print("=" * 80 + "\n")


def main():
    service = IPSAKTIService()

    queries = [
        ("Is turmeric + neem patentable in India?", "Query 1: Turmeric + Neem Patentability"),
        ("AYUSH licensing steps under Rule 158-B", "Query 2: AYUSH Rule 158-B Licensing"),
        ("ABS obligations under Biodiversity Act", "Query 3: ABS Biodiversity Obligations"),
        ("क्या भारत में हल्दी और नीम का पेटेंट कराया जा सकता है?", "Query 4: Hindi Turmeric + Neem Query"),
    ]

    for q_text, q_label in queries:
        trace_query(service, q_text, q_label)


if __name__ == "__main__":
    main()
