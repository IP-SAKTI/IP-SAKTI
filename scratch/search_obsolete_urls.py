from pathlib import Path

root = Path(".")
matches = []

for p in root.rglob("*"):
    if p.is_file() and not any(part.startswith(".") or part in ("node_modules", "__pycache__", "indexes", "db") for part in p.parts):
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            if "patents.htm" in content or "www.ipindia.gov.in" in content:
                matches.append((str(p), [line for line in content.splitlines() if "patents.htm" in line or "www.ipindia.gov.in" in line]))
        except Exception:
            pass

print(f"Found {len(matches)} files containing obsolete URLs:")
for fpath, lines in matches:
    print(f"File: {fpath}")
    for l in lines:
        print(f"   {l.strip()}")
