"""
Debug script to inspect Cosine Similarity and Bayesian Confidence for the query:
"Find patents related to Ashwagandha formulations."
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest, Jurisdiction, FormulationCategory
from ip_sakti.retrieval.pipeline import HybridRAGPipeline

def main():
    print("=== DEBUGGING QUERY: 'Find patents related to Ashwagandha formulations.' ===")
    
    # 1. Test raw FAISS search directly on HybridRAGPipeline
    pipeline = HybridRAGPipeline()
    try:
        pipeline.load_index()
        print(f"Loaded HybridRAG index. Total FAISS vectors: {pipeline.faiss_store.num_vectors}")
    except Exception as e:
        print(f"Index load error: {e}")

    query_str = "Find patents related to Ashwagandha formulations."
    
    query_vec = pipeline.embedding_generator.embed_query(query_str)
    faiss_raw_results = pipeline.faiss_store.search(query_vec, top_k=5)
    print("\n--- Direct Top 5 FAISS Vector Similarity Results ---")
    for idx, (doc, score) in enumerate(faiss_raw_results, 1):
        print(f"{idx}. Doc ID: {doc.doc_id}")
        print(f"   Title:  {doc.title}")
        print(f"   Cosine: {score:.6f}")
        print(f"   Snippet: {doc.content[:100]!r}")

    # 2. Test Hybrid RAG Pipeline search
    rag_evidence = pipeline.search(query_str)
    print("\n--- Hybrid RAG Pipeline Output (After RRF & Cross-Encoder Reranking) ---")
    for idx, chunk in enumerate(rag_evidence, 1):
        print(f"{idx}. Doc ID: {chunk.doc_id}")
        print(f"   Title:        {chunk.title}")
        print(f"   FAISS Cosine: {chunk.faiss_score}")
        print(f"   BM25 Score:   {chunk.bm25_score}")
        print(f"   RRF Score:    {chunk.rrf_score}")
        print(f"   Rerank Score: {chunk.rerank_score}")

    # 3. Test Full IPSAKTIService process_query
    service = IPSAKTIService()
    req = QueryRequest(
        raw_query=query_str,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.CLASSICAL
    )
    res = service.process_query(req)
    
    print("\n--- Full IPSAKTIService Process Query Result ---")
    print(f"Evidence Count: {len(res.evidence)}")
    print("Top 5 Evidence Chunks in FinalResponse:")
    for idx, chunk in enumerate(res.evidence, 1):
        print(f"{idx}. Doc ID: {chunk.doc_id}")
        print(f"   Title:        {chunk.title}")
        print(f"   FAISS Cosine: {chunk.faiss_score}")
        print(f"   Rerank Score: {chunk.rerank_score}")
        print(f"   Source Name:  {chunk.source_name}")

    if res.evidence:
        faiss_scores = [c.faiss_score for c in res.evidence if c.faiss_score is not None]
        print(f"\nAll FAISS scores in final evidence: {faiss_scores}")
        if faiss_scores:
            print(f"max(faiss_scores) in final evidence: {max(faiss_scores)}")

    if res.confidence:
        print(f"Confidence Score: {res.confidence.score}")
        print(f"Confidence Percentage: {res.confidence.confidence_percentage}%")
        print(f"Confidence Level: {res.confidence.confidence_level}")
        print(f"Confidence Signals: {res.confidence.signals}")

if __name__ == "__main__":
    main()
