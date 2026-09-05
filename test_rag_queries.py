from ip_sakti.retrieval.pipeline import HybridRAGPipeline

rag = HybridRAGPipeline()
rag.load_index()

queries = [
    "What form is required to apply for a licence to manufacture Ayurvedic drugs for sale?",
    "What does Section 3(p) of the Patents Act say about traditional knowledge?",
    "What are the access and benefit-sharing obligations under the Biological Diversity Act?",
    "What is the role of TKDL in preventing patents on traditional knowledge?",
    "What are the requirements under Rule 158-B for AYUSH manufacturing?",
]

for q in queries:
    print("\n" + "=" * 80)
    print("QUERY:", q)
    print("=" * 80)

    results = rag.search(q, rerank_top_k=3)

    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r.title}")
        print("   Source:", r.source_name)
        print("   Rerank:", round(r.rerank_score, 3))
        print("   Content:", r.content[:500].replace("\n", " "))
