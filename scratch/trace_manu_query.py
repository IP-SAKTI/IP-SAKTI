import os
import sys

sys.path.insert(0, ".")

from ip_sakti.models.query import QueryRequest
from ip_sakti.multilingual import MultilingualService
from ip_sakti.orchestrator import Orchestrator
from ip_sakti.rule_engine import AgentRouter, RuleEngine
from ip_sakti.retrieval import HybridRAGPipeline
from ip_sakti.agents import IPAgent, RegulatoryAgent, TKABSAgent
from ip_sakti.llm import AnswerSynthesisService
from ip_sakti.pipeline import PipelineCoordinator

def trace_query(raw_query_str: str):
    print("=" * 80)
    print(f"TRACE FOR QUERY: {raw_query_str!r}")
    print("=" * 80)

    os.environ["HF_HUB_OFFLINE"] = "1"

    req = QueryRequest(raw_query=raw_query_str)
    print(f"1. Raw Query: {req.raw_query}")

    # Stage 2: Multilingual Service
    ms = MultilingualService()
    m_ctx = ms.process(req)
    print(f"2. Detected Language: {m_ctx.detection.language} (conf: {m_ctx.detection.confidence})")
    print(f"3. Normalized Query: {m_ctx.normalisation.normalised}")
    print(f"4. Translated Query: {m_ctx.query_translation.translated_text}")

    # Stage 4: Orchestrator
    orch = Orchestrator()
    q_ctx = orch.process(req, m_ctx)
    print(f"5. Orchestrator Intent: {q_ctx.intent}")
    print(f"6. Jurisdiction: {q_ctx.jurisdiction}, Formulation: {q_ctx.formulation_category}")

    # Agent Router
    router = AgentRouter()
    target_agents = router.route(q_ctx)
    print(f"7. Selected Agents: {[a.value for a in target_agents]}")

    # Hybrid RAG Pipeline
    rag = HybridRAGPipeline()
    if not rag.is_built:
        rag.load_index()

    # Trace agents execution
    agents = {
        "ip_agent": IPAgent(),
        "regulatory_agent": RegulatoryAgent(),
        "tk_abs_agent": TKABSAgent(),
    }

    # Also trace direct RAG search with translated query
    clean_query = q_ctx.translated_query
    query_vector = rag.embedding_generator.embed_query(clean_query)
    faiss_res = rag.faiss_store.search(query_vector, top_k=5)
    print("\n8. FAISS Candidates for clean query:")
    for c, score in faiss_res:
        print(f"   [doc_id: {c.doc_id}] score: {score:.4f} | content snippet: {c.content[:80]!r}")

    bm25_res = rag.bm25_store.search(clean_query, top_k=5)
    print("\n9. BM25 Candidates for clean query:")
    for c, score in bm25_res:
        print(f"   [doc_id: {c.doc_id}] score: {score:.4f} | content snippet: {c.content[:80]!r}")

    fused = rag.fusion.fuse(faiss_res, bm25_res)
    print("\n10. RRF Candidates for clean query:")
    for fc in fused:
        print(f"   [doc_id: {fc.chunk.doc_id}] rrf_score: {fc.rrf_score:.4f} faiss: {fc.faiss_score} bm25: {fc.bm25_score}")

    reranked = rag.reranker.rerank(clean_query, fused, top_k=5)
    print("\n11. Cross-Encoder scores for clean query:")
    for fc, score in reranked:
        print(f"   [doc_id: {fc.chunk.doc_id}] cross-encoder score: {score:.4f} | title: {fc.chunk.title}")

    # Agent execution search queries
    print("\nTracing Agent Search Queries:")
    for agent_type in target_agents:
        agent = agents.get(agent_type.value)
        if agent:
            # Let's inspect what query the agent passes to rag.search
            if agent_type.value == "ip_agent":
                ip_keywords = ["patent", "prior art", "section 3", "claim", "cgdptm", "wipo", "novelty"]
                sq = clean_query
                if sq and not any(kw in sq.lower() for kw in ip_keywords):
                    sq = f"{sq} patent patentability section 3(p) prior art"
                print(f"   IPAgent modified search query: {sq!r}")
                agent_evidence = rag.search(sq)
                print(f"   IPAgent returned {len(agent_evidence)} evidence chunks")
                for chk in agent_evidence:
                    print(f"      [chunk_id: {chk.chunk_id}] rerank: {chk.rerank_score:.4f} faiss: {chk.faiss_score} bm25: {chk.bm25_score}")

    # Full coordinator execution
    coord = PipelineCoordinator()
    res = coord.execute(req)
    print("\n15. Final Response:")
    print(f"    is_abstention: {res.is_abstention}")
    print(f"    confidence: {res.confidence}")
    print(f"    agents_invoked: {[a.value for a in res.agents_invoked]}")
    print(f"    evidence_count: {len(res.evidence)}")
    print(f"    answer:\n{res.answer}")

if __name__ == "__main__":
    trace_query("who is manu")
