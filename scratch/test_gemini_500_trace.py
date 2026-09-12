"""
scratch/test_gemini_500_trace.py — Script to trace exact Gemini API call & backend failure for:
"Is a formulation containing turmeric and neem patentable in India, considering the Traditional Knowledge exclusion under Section 3(p)?"
"""

import sys
import os
import traceback
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest, Jurisdiction, FormulationCategory
from ip_sakti.llm.gemini_adapter import GeminiLLMAdapter

def main():
    query_str = "Is a formulation containing turmeric and neem patentable in India, considering the Traditional Knowledge exclusion under Section 3(p)?"
    print(f"=== TRACING EXACT BACKEND & GEMINI FAILURE ===")
    print(f"Query: {query_str!r}\n")

    # 1. Inspect Gemini Adapter configuration
    adapter = GeminiLLMAdapter()
    print(f"Configured Model Name: {adapter.model_name!r}")
    print(f"GenAI Available:      {adapter._configured}")
    print(f"API Key Present:      {bool(adapter.api_key)}")

    # 2. Test Full Service process_query
    print("\n--- Running IPSAKTIService process_query ---")
    try:
        service = IPSAKTIService()
        req = QueryRequest(
            raw_query=query_str,
            jurisdiction=Jurisdiction.INDIA,
            formulation_category=FormulationCategory.CLASSICAL
        )
        res = service.process_query(req)
        print("process_query COMPLETED SUCCESSFULLY!")
        print(f"Answer (first 150 chars): {res.answer[:150]!r}")
        print(f"Is Abstention: {res.is_abstention}")
        print(f"Evidence Count: {len(res.evidence)}")
        if res.confidence:
            print(f"Confidence Score: {res.confidence.score}")
    except Exception as exc:
        print("\n!!! CAUGHT EXCEPTION IN PROCESS_QUERY !!!")
        print(f"Exception Type: {type(exc).__name__}")
        print(f"Exception Message: {exc}")
        print("\nFull Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
