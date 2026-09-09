"""
scratch/sih_20_query_benchmark.py — SIH 2026 20-Query Benchmark & RAG Evaluation Script.

Executes 20 representative queries across IP, AYUSH, TK/ABS, Multilingual, and Abstention domains.
Captures domain classification, top evidence, citation coverage, confidence score, abstention status, and latency.
"""

import json
import logging
import os
import sys
import time
import requests
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sih_benchmark")

BASE_URL = "http://localhost:8000"

BENCHMARK_QUERIES = [
    # Category 1: Indian IP / Patents (5 queries)
    {
        "id": "IP-01",
        "category": "Indian IP / Patents",
        "query": "What are the patentability considerations for an Ayurvedic formulation containing turmeric under Section 3(p)?",
        "expected_domain": "IP"
    },
    {
        "id": "IP-02",
        "category": "Indian IP / Patents",
        "query": "Does a mere admixture of known medicinal plants qualify for patent grant under Section 3(e) of the Indian Patents Act?",
        "expected_domain": "IP"
    },
    {
        "id": "IP-03",
        "category": "Indian IP / Patents",
        "query": "What are the disclosure requirements for biological material under Section 10(4)(d)(ii) of the Indian Patents Act?",
        "expected_domain": "IP"
    },
    {
        "id": "IP-04",
        "category": "Indian IP / Patents",
        "query": "How does the Indian Patent Office use the Traditional Knowledge Digital Library (TKDL) to establish prior art?",
        "expected_domain": "IP"
    },
    {
        "id": "IP-05",
        "category": "Indian IP / Patents",
        "query": "Can a synergistic combination of herbal extracts be patented in India if non-obviousness is proven?",
        "expected_domain": "IP"
    },

    # Category 2: AYUSH Regulatory Compliance (5 queries)
    {
        "id": "AYUSH-01",
        "category": "AYUSH Regulatory",
        "query": "What are the mandatory proof of safety requirements under Rule 158-B of Drugs and Cosmetics Rules for Ayurvedic proprietary medicine?",
        "expected_domain": "AYUSH"
    },
    {
        "id": "AYUSH-02",
        "category": "AYUSH Regulatory",
        "query": "What is the procedure and documentation required to apply for Form 24D manufacturing license for ASU medicines?",
        "expected_domain": "AYUSH"
    },
    {
        "id": "AYUSH-03",
        "category": "AYUSH Regulatory",
        "query": "What are the labeling and quality control guidelines prescribed by the Ministry of AYUSH for classical formulations?",
        "expected_domain": "AYUSH"
    },
    {
        "id": "AYUSH-04",
        "category": "AYUSH Regulatory",
        "query": "Do classical Ayurvedic medicines listed in authoritative texts require clinical trials under Rule 158-B?",
        "expected_domain": "AYUSH"
    },
    {
        "id": "AYUSH-05",
        "category": "AYUSH Regulatory",
        "query": "What are the compliance requirements for selling Ayurvedic proprietary cosmetics vs therapeutic formulations in India?",
        "expected_domain": "AYUSH"
    },

    # Category 3: TK / Access & Benefit Sharing (5 queries)
    {
        "id": "TKABS-01",
        "category": "TK / ABS",
        "query": "When is prior approval from the National Biodiversity Authority (NBA) mandatory under the Biological Diversity Act, 2002?",
        "expected_domain": "TK_ABS"
    },
    {
        "id": "TKABS-02",
        "category": "TK / ABS",
        "query": "What are the benefit-sharing obligations for commercial utilization of biological resources under NBA ABS Regulations 2014?",
        "expected_domain": "TK_ABS"
    },
    {
        "id": "TKABS-03",
        "category": "TK / ABS",
        "query": "Can a foreign entity file a patent in India using Indian bio-resources without prior NBA consent?",
        "expected_domain": "TK_ABS"
    },
    {
        "id": "TKABS-04",
        "category": "TK / ABS",
        "query": "What is the role of State Biodiversity Boards (SBB) in access and benefit sharing for Indian citizens?",
        "expected_domain": "TK_ABS"
    },
    {
        "id": "TKABS-05",
        "category": "TK / ABS",
        "query": "What are the penalties for accessing Indian biological resources for commercial research without NBA approval under Section 55?",
        "expected_domain": "TK_ABS"
    },

    # Category 4: Multilingual Indic Queries (3 queries)
    {
        "id": "MULTI-01",
        "category": "Multilingual (Hindi)",
        "query": "आयुर्वेदिक औषधि के लिए पेटेंट दाखिल करने की क्या आवश्यकताएँ हैं?",
        "expected_domain": "IP"
    },
    {
        "id": "MULTI-02",
        "category": "Multilingual (Hindi)",
        "query": "क्या हल्दी और नीम के पारंपरिक उपयोग पर भारत में पेटेंट मिल सकता है?",
        "expected_domain": "IP"
    },
    {
        "id": "MULTI-03",
        "category": "Multilingual (Hindi)",
        "query": "एनबीए (NBA) से जैविक संसाधनों के उपयोग के लिए अनुमति कब आवश्यक है?",
        "expected_domain": "TK_ABS"
    },

    # Category 5: Insufficient Evidence / Out-of-Domain (2 queries)
    {
        "id": "OUT-01",
        "category": "Out-of-Domain (Abstention)",
        "query": "What are the cryptographic quantum key distribution protocols specified in the Indian IT Act 2000?",
        "expected_domain": "OUT_OF_DOMAIN"
    },
    {
        "id": "OUT-02",
        "category": "Out-of-Domain (Abstention)",
        "query": "What is the exact chemical synthesis procedure for synthetic mRNA vaccines under FDA 2026 regulations?",
        "expected_domain": "OUT_OF_DOMAIN"
    }
]

def run_benchmark():
    print("=" * 100)
    print("      IP-SAKTI SAHAYAK — SIH 2026 20-QUERY EVALUATION BENCHMARK & MULTI-AGENT AUDIT      ")
    print("=" * 100)

    # Health Check
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, "Backend FastAPI is unreachable"
    print("[PASS] System Health: FastAPI backend is active.\n")

    results = []
    total_latency = 0.0

    for idx, item in enumerate(BENCHMARK_QUERIES, 1):
        q_id = item["id"]
        cat = item["category"]
        q_text = item["query"]

        start_time = time.time()
        res = requests.post(f"{BASE_URL}/query", json={"raw_query": q_text})
        elapsed = time.time() - start_time
        total_latency += elapsed

        if res.status_code != 200:
            print(f"[{q_id}] ERROR ({res.status_code}): {res.text}")
            continue

        data = res.json()

        confidence = data.get("confidence")
        is_abstention = data.get("is_abstention", False)
        evidence_list = data.get("evidence", [])
        citations_list = data.get("citations", [])
        agents = data.get("agents_invoked", [])
        answer = data.get("answer", "")

        top_doc_ids = [e.get("doc_id") or e.get("source_id") for e in evidence_list[:3]]

        record = {
            "num": idx,
            "id": q_id,
            "category": cat,
            "query": q_text,
            "agents": agents,
            "evidence_count": len(evidence_list),
            "top_docs": top_doc_ids,
            "citation_count": len(citations_list),
            "confidence": confidence,
            "is_abstention": is_abstention,
            "latency_sec": round(elapsed, 2),
            "answer_snippet": answer[:120].replace("\n", " ") + "..."
        }
        results.append(record)

        conf_str = f"{(confidence * 100):.2f}%" if isinstance(confidence, (int, float)) else str(confidence)
        abst_str = "ABSTAINED" if is_abstention else "ANSWERED"

        print(f"[{q_id}] ({cat}) | Status: {abst_str} | Confidence: {conf_str} | Latency: {elapsed:.2f}s")
        print(f"       Agents: {agents} | Top Evidence: {top_doc_ids}")
        print(f"       Snippet: {record['answer_snippet']}\n")

    avg_latency = total_latency / len(BENCHMARK_QUERIES)

    print("=" * 100)
    print("                             BENCHMARK SUMMARY METRICS                             ")
    print("=" * 100)
    print(f"Total Queries Executed : {len(results)} / 20")
    print(f"Average Latency        : {avg_latency:.2f} seconds per query")
    print(f"Answered Queries       : {sum(1 for r in results if not r['is_abstention'])}")
    print(f"Safely Abstained       : {sum(1 for r in results if r['is_abstention'])}")
    print("=" * 100)

    with open("scratch/sih_20_query_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n[SUCCESS] Detailed benchmark results saved to scratch/sih_20_query_results.json")

if __name__ == "__main__":
    run_benchmark()
