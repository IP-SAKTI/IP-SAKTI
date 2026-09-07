import httpx
import json

url = "http://localhost:8000/query"
payload = {
    "raw_query": "who is manu",
    "jurisdiction": "unknown",
    "formulation_category": "unknown",
    "user_language": None,
}

print(f"Sending POST to {url} with payload: {payload}")
try:
    resp = httpx.post(url, json=payload, timeout=10.0)
    print(f"HTTP Status: {resp.status_code}")
    print("Response JSON:")
    print(json.dumps(resp.json(), indent=2))
except Exception as exc:
    print(f"Error calling API: {exc}")
