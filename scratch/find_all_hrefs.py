import os
import re
from pathlib import Path

root_dir = Path("d:/Project/IP-SAKTI")

print("=== 1. Searching for any mention of patents.htm ===")
for path in root_dir.rglob("*"):
    if path.is_file() and not any(part.startswith(".") or part in ("node_modules", ".venv", "__pycache__") for part in path.parts):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "patents.htm" in text.lower():
                print(f"File: {path}")
                for i, line in enumerate(text.splitlines(), 1):
                    if "patents.htm" in line.lower():
                        print(f"  Line {i}: {line.strip()}")
        except Exception:
            pass

print("\n=== 2. Searching for any mention of www.ipindia.gov.in ===")
for path in root_dir.rglob("*"):
    if path.is_file() and not any(part.startswith(".") or part in ("node_modules", ".venv", "__pycache__") for part in path.parts):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "www.ipindia.gov.in" in text.lower():
                print(f"File: {path}")
                for i, line in enumerate(text.splitlines(), 1):
                    if "www.ipindia.gov.in" in line.lower():
                        print(f"  Line {i}: {line.strip()}")
        except Exception:
            pass

print("\n=== 3. Searching for 'Open official' or 'external' in UI files ===")
ui_dir = root_dir / "ip_sakti" / "ui"
for path in ui_dir.rglob("*.py"):
    text = path.read_text(encoding="utf-8", errors="ignore")
    for i, line in enumerate(text.splitlines(), 1):
        if any(term in line.lower() for term in ["official", "external", "source_url", "doc_link", "href"]):
            print(f"File {path.name}: L{i}: {line.strip()}")
