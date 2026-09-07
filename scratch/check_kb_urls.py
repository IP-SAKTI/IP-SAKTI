import json
from pathlib import Path

knowledge_dir = Path("data/knowledge")

for fpath in sorted(knowledge_dir.glob("*.json")):
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    doc_id = data.get("doc_id")
    meta = data.get("metadata", {})
    print(f"File: {fpath.name}")
    print(f"  doc_id: {doc_id}")
    print(f"  source_id: {meta.get('source_id')}")
    print(f"  source_url: {meta.get('source_url')}")
    print(f"  canonical_url: {meta.get('canonical_url')}")
    print("-" * 50)
