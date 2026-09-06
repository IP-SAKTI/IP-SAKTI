import sys
import json
import logging
from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest, Jurisdiction, FormulationCategory

logging.basicConfig(level=logging.INFO)

def test_query():
    service = IPSAKTIService()
    req = QueryRequest(
        raw_query="What form is required to apply for a licence to manufacture Ayurvedic drugs for sale?",
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.UNKNOWN,
        user_language="en",
    )
    res = service.process_query(req)
    print("="*60)
    print("ANSWER:")
    print(res.answer)
    print("="*60)
    print("EVIDENCE CHUNKS:")
    for i, chunk in enumerate(res.evidence, 1):
        print(f"--- Chunk {i} ---")
        print(f"chunk_id: {chunk.chunk_id}")
        print(f"doc_id: {chunk.doc_id}")
        print(f"source_id: {chunk.source_id}")
        print(f"source_label: {chunk.source_label}")
        print(f"source_url: {chunk.source_url}")
        print(f"title: {chunk.title}")
        print(f"content length: {len(chunk.content)}")
    
if __name__ == "__main__":
    test_query()
