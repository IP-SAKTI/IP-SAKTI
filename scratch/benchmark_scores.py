import os
import sys

sys.path.insert(0, ".")

from ip_sakti.retrieval import HybridRAGPipeline

os.environ["HF_HUB_OFFLINE"] = "1"

rag = HybridRAGPipeline()
if not rag.is_built:
    rag.load_index()

queries = [
    ("VALID 1", "what form is required to manufacture Ayurvedic drugs for sale?"),
    ("VALID 2", "What are the licensing requirements under Rule 158-B for manufacturing Ayurvedic drugs?"),
    ("VALID 3", "How does TKDL help prevent patents based on traditional Indian knowledge?"),
    ("VALID 4", "What is Section 3(p) of the Indian Patents Act?"),
    ("INVALID 1", "who is manu"),
    ("INVALID 2", "what is the capital of France"),
    ("INVALID 3", "who is Elon Musk"),
    ("INVALID 4", "how do I repair my laptop"),
    ("INVALID 5", "tell me a joke"),
    ("INVALID 6", "xyzabc123"),
]

print("=" * 100)
print(f"{'CATEGORY':<12} | {'QUERY':<50} | {'MAX CE':<8} | {'AVG CE':<8} | {'TOP CHUNK TITLE'}")
print("=" * 100)

for cat, q in queries:
    # Get RRF fused candidates for clean query
    query_vector = rag.embedding_generator.embed_query(q)
    faiss_res = rag.faiss_store.search(query_vector, top_k=10)
    bm25_res = rag.bm25_store.search(q, top_k=10)
    fused = rag.fusion.fuse(faiss_res, bm25_res)
    
    if not fused:
        print(f"{cat:<12} | {q:<50} | {'N/A':<8} | {'N/A':<8} | No candidates")
        continue

    reranked = rag.reranker.rerank(q, fused, top_k=5)
    
    if reranked:
        scores = [score for cand, score in reranked]
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        top_title = reranked[0][0].chunk.title or "Untitled"
        print(f"{cat:<12} | {q[:50]:<50} | {max_score:<8.4f} | {avg_score:<8.4f} | {top_title[:30]}")
    else:
        print(f"{cat:<12} | {q[:50]:<50} | {'N/A':<8} | {'N/A':<8} | None")
