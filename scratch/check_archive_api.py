import urllib.request
import json
import re

print("=== 1. Checking JSON format response ===")
json_url = "http://127.0.0.1:8000/document/ip_india_patents_act_3p?format=json"
with urllib.request.urlopen(json_url) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print(f"source_id: {data.get('source_id')}")
    print(f"official_url: {data.get('official_url')}")
    print(f"archive_url: {data.get('archive_url')}")
    print(f"is_valid_archive_url: {data.get('is_valid_archive_url')}")

print("\n=== 2. Checking HTML format response ===")
html_url = "http://127.0.0.1:8000/document/ip_india_patents_act_3p?format=html"
with urllib.request.urlopen(html_url) as resp:
    html_text = resp.read().decode('utf-8')
    match_official = re.search(r'href="([^"]+)"[^>]*class="btn-official"', html_text)
    match_archive = re.search(r'href="([^"]+)"[^>]*class="btn-archive"', html_text)
    print(f"Official button link: {match_official.group(1) if match_official else None}")
    print(f"Archive button link: {match_archive.group(1) if match_archive else None}")
