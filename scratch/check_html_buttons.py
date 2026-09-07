import urllib.request
import re

urls = [
    "http://127.0.0.1:8000/document/ip_india_patents_act_3p?format=html",
    "http://127.0.0.1:8000/document/ip_india_ayush_guidelines_2025?format=html",
    "http://127.0.0.1:8000/document/ayush_rule_158b?format=html",
    "http://127.0.0.1:8000/document/tkdl_wipo_policy?format=html"
]

for url in urls:
    try:
        with urllib.request.urlopen(url) as resp:
            content = resp.read().decode('utf-8')
            match = re.search(r'href="([^"]+)"[^>]*class="btn-official"', content)
            if match:
                print(f"URL: {url} -> Official Link: {match.group(1)}")
            else:
                print(f"URL: {url} -> No btn-official match")
    except Exception as e:
        print(f"Error {url}: {e}")
