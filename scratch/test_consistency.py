"""
scratch/test_consistency.py — Test 5 consecutive runs of the same query for RAG determinism.
"""

import requests
import json

BASE_URL = "http://localhost:8000"
QUERY = "Is turmeric + neem patentable in India?"

def main():
    print("Testing 5-run determinism for query:", QUERY)
    results = []

    for i in range(1, 6):
        resp = requests.post(f"{BASE_URL}/query", json={"raw_query": QUERY})
        assert resp.status_code == 200, f"Run {i} failed: {resp.text}"
        data = resp.json()
        top_ev = data["evidence"][0]["doc_id"] if data["evidence"] else "None"
        conf = data["confidence"]
        results.append({
            "run": i,
            "query_id": data.get("query_id"),
            "top_doc_id": top_ev,
            "confidence": conf,
            "is_abstention": data["is_abstention"],
            "citation_count": len(data["citations"])
        })
        print(f"Run {i}: Top Evidence={top_ev} | Conf={conf} | Abstain={data['is_abstention']}")

    first_doc = results[0]["top_doc_id"]
    first_conf = results[0]["confidence"]

    for r in results:
        assert r["top_doc_id"] == first_doc, f"Mismatch in top doc ID at run {r['run']}"
        assert r["confidence"] == first_conf, f"Mismatch in confidence score at run {r['run']}"

    print("ALL 5 RUNS PRODUCED 100% IDENTICAL RETRIEVAL AND CONFIDENCE SCORES!")

if __name__ == "__main__":
    main()
