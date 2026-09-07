import os
import sys

# Ensure PYTHONPATH includes workspace
sys.path.insert(0, ".")

from ip_sakti.models.query import QueryRequest
from ip_sakti.pipeline import PipelineCoordinator

def test_debug_query(query_str: str):
    print(f"\n==========================================")
    print(f"DEBUG QUERY: {query_str!r}")
    print(f"==========================================")

    os.environ["HF_HUB_OFFLINE"] = "1"
    coordinator = PipelineCoordinator()

    req = QueryRequest(raw_query=query_str)
    res = coordinator.execute(req)

    print(f"Is Abstention: {res.is_abstention}")
    if res.confidence:
        print(f"Confidence Score: {res.confidence.score}")
        print(f"Citation Coverage: {res.confidence.citation_coverage}")
        print(f"Avg Rerank Score: {res.confidence.avg_rerank_score}")
        print(f"Evidence Count: {res.confidence.evidence_count}")
        print(f"Reason: {res.confidence.reason}")
    else:
        print("Confidence: None")

    print(f"Agents Invoked: {[a.value for a in res.agents_invoked]}")
    print(f"Evidence count: {len(res.evidence)}")
    for idx, chunk in enumerate(res.evidence, 1):
        print(f"  Chunk {idx}: faiss={chunk.faiss_score:.4f}, bm25={chunk.bm25_score}, rerank={chunk.rerank_score}")
    
    print(f"\nAnswer:\n{res.answer}")

if __name__ == "__main__":
    test_debug_query("manu anuty")
    test_debug_query("What is the capital of France?")
    test_debug_query("How do I repair my laptop?")
