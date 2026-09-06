import httpx
import sys

API_BASE_URL = "http://localhost:8000"

def test_full_flow():
    queries = [
        "What form is required to apply for a licence to manufacture Ayurvedic drugs for sale?",
        "What are the requirements under Rule 158-B for manufacturing Ayurvedic medicines?",
        "What is the role of the National Biodiversity Authority in access and benefit sharing?",
        "How does the Traditional Knowledge Digital Library help prevent wrongful patents based on Indian traditional knowledge?",
        "What is the exact government fee for registering a new Ayurvedic patent in Antarctica?",
    ]

    for q in queries:
        print("=" * 80)
        print(f"QUERY: {q}")
        payload = {
            "raw_query": q,
            "jurisdiction": "india",
            "formulation_category": "unknown",
            "user_language": "en"
        }
        res = httpx.post(f"{API_BASE_URL}/query", json=payload, timeout=30.0)
        assert res.status_code == 200, f"Query failed: {res.status_code}"
        data = res.json()
        
        print(f"Is Abstention: {data.get('is_abstention')}")
        conf_score = (data.get("confidence") or {}).get("score", 0.0)
        print(f"Confidence Score: {conf_score}")
        print("--- ANSWER ---")
        print(data.get("answer"))
        print("--- EVIDENCE CHUNKS & LOCAL VIEWER LINKS ---")
        for chunk in data.get("evidence", []):
            sid = chunk.get("source_id") or chunk.get("doc_id")
            doc_link = f"{API_BASE_URL}/document/{sid}"
            # Test document viewer endpoint (returns HTTP 200 HTML)
            doc_res = httpx.get(doc_link, follow_redirects=False)
            print(f"Chunk [{chunk.get('source_label')}] sid={sid} -> HTTP {doc_res.status_code} Content-Type={doc_res.headers.get('content-type')} Length={len(doc_res.content)}")
            assert doc_res.status_code == 200, f"Failed document link for {sid}: {doc_res.status_code}"
            assert "application/pdf" in doc_res.headers.get("content-type", "").lower()
            assert doc_res.content.startswith(b"%PDF")

            # Test JSON format parameter
            json_res = httpx.get(f"{doc_link}?format=json", follow_redirects=False)
            assert json_res.status_code == 200
            jdata = json_res.json()
            print(f"  --> JSON viewer -> title: {jdata.get('title')!r} | official_url: {jdata.get('official_url')}")

    # Test unknown ID -> 404
    err_res = httpx.get(f"{API_BASE_URL}/document/nonexistent")
    print(f"Nonexistent ID -> HTTP {err_res.status_code}")
    assert err_res.status_code == 404

if __name__ == "__main__":
    test_full_flow()
