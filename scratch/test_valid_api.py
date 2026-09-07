import httpx
import json

url = "http://localhost:8000/query"
payload = {
    "raw_query": "What form is required to apply for a licence to manufacture Ayurvedic drugs for sale?",
    "jurisdiction": "unknown",
    "formulation_category": "unknown",
    "user_language": None,
}

print(f"Sending POST to {url} with valid query payload...")
resp = httpx.post(url, json=payload, timeout=20.0)
print(f"HTTP Status: {resp.status_code}")
data = resp.json()
print(f"is_abstention: {data.get('is_abstention')}")
print(f"confidence score: {data.get('confidence', {}).get('score') if data.get('confidence') else None}")
print(f"evidence count: {len(data.get('evidence', []))}")
print(f"answer preview: {data.get('answer', '')[:200]}...")
