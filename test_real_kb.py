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

    for i, r in enumerate(results):
        print(f"\n{i + 1}. {r.title}")
        print(f"   Source: {r.source_name}")
        print(f"   Score:  {r.rerank_score:.3f}")
        print(f"   URL:    {r.source_url}")
        print(f"   Text:   {r.content[:500].replace(chr(10), ' ')}")
