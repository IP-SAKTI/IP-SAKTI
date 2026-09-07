import json
from pathlib import Path

config_file = Path("config/sources.json")
knowledge_dir = Path("data/knowledge")

with open(config_file, "r", encoding="utf-8") as f:
    sources = json.load(f)

source_map = {s["source_id"]: s for s in sources}

for fpath in knowledge_dir.glob("*.json"):
    with open(fpath, "r", encoding="utf-8") as f:
        doc = json.load(f)
    
    meta = doc.get("metadata", {})
    sid = meta.get("source_id")
    
    if not sid:
        doc_id = doc.get("doc_id", "")
        if doc_id.startswith("doc_"):
            sid = doc_id[4:]
        else:
            sid = doc_id
            
    if sid in source_map:
        s_meta = source_map[sid]
        meta["source_url"] = s_meta["url"]
        if "canonical_url" in s_meta:
            meta["canonical_url"] = s_meta["canonical_url"]
        if "archive_url" in s_meta:
            meta["archive_url"] = s_meta["archive_url"]
        doc["metadata"] = meta
        
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2)
        print(f"Updated {fpath.name} for source_id: {sid}")
    else:
        print(f"Skipped {fpath.name}: source_id {sid} not in config")
