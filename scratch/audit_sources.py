import json
import urllib.request
import urllib.error
import ssl
from pathlib import Path

CONFIG_PATH = Path("config/sources.json")
KNOWLEDGE_DIR = Path("data/knowledge")

def check_url(url):
    # Context that validates SSL certificate strictly first
    strict_ctx = ssl.create_default_context()
    # Context that ignores SSL errors to diagnose if certificate is the only issue
    unverified_ctx = ssl._create_unverified_context()
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    req = urllib.request.Request(url, headers=headers)
    
    result = {
        "url": url,
        "status": None,
        "strict_ssl": False,
        "final_url": None,
        "error": None
    }
    
    # Try strict SSL first
    try:
        with urllib.request.urlopen(req, timeout=10, context=strict_ctx) as response:
            result["status"] = response.status
            result["strict_ssl"] = True
            result["final_url"] = response.url
            return result
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["final_url"] = e.url
        result["error"] = f"HTTPError {e.code}: {e.reason}"
        return result
    except urllib.error.URLError as e:
        result["error"] = f"URLError: {e.reason}"
        # Check if it was SSL error
        if isinstance(e.reason, ssl.SSLError):
            result["ssl_error"] = str(e.reason)
            # Try unverified to check if path exists
            try:
                with urllib.request.urlopen(req, timeout=10, context=unverified_ctx) as u_resp:
                    result["status"] = u_resp.status
                    result["final_url"] = u_resp.url
                    result["unverified_worked"] = True
            except Exception as u_e:
                result["unverified_error"] = str(u_e)
        return result
    except Exception as e:
        result["error"] = f"Exception: {str(e)}"
        return result

def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        sources = json.load(f)

    print(f"Auditing {len(sources)} sources from {CONFIG_PATH}...\n")

    for idx, s in enumerate(sources, 1):
        source_id = s.get("source_id")
        title = s.get("title")
        authority = s.get("organisation")
        url = s.get("url")
        canonical_url = s.get("canonical_url")
        
        print(f"[{idx}/{len(sources)}] Source ID: {source_id}")
        print(f"    Authority: {authority}")
        print(f"    Title: {title}")
        print(f"    Configured URL: {url}")
        if canonical_url:
            print(f"    Canonical URL: {canonical_url}")
        
        res = check_url(url)
        print(f"    Strict SSL OK: {res['strict_ssl']}")
        print(f"    Status: {res['status']}")
        print(f"    Final URL: {res['final_url']}")
        if res.get("error"):
            print(f"    Error: {res['error']}")
        if res.get("ssl_error"):
            print(f"    SSL Error Details: {res['ssl_error']}")
        
        if canonical_url:
            c_res = check_url(canonical_url)
            print(f"    [Canonical Check] Strict SSL OK: {c_res['strict_ssl']}, Status: {c_res['status']}, Final URL: {c_res['final_url']}")
            if c_res.get("error"):
                print(f"    [Canonical Check] Error: {c_res['error']}")
        print("-" * 60)

if __name__ == "__main__":
    main()
