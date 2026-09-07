import urllib.request
import json

urls = [
    "http://127.0.0.1:8000/document/doc_ip_india_ayush_guidelines_2025?format=json",
    "http://127.0.0.1:8000/document/doc_ip_india_ayush_guidelines_2025",
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            print("URL:", url)
            print("Status:", resp.status)
            print("Content-Type:", resp.headers.get("Content-Type"))
            body = resp.read().decode("utf-8", errors="ignore")
            if "json" in resp.headers.get("Content-Type", ""):
                print("JSON Data:", json.dumps(json.loads(body), indent=2))
            else:
                print("HTML Body preview:", body[:300])
            print("-" * 60)
    except Exception as e:
        print("URL:", url)
        print("Error:", e)
        print("-" * 60)
