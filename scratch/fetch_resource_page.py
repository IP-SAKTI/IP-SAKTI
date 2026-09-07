import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://ipindia.gov.in/resource/patents-resources-guidelines"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("Page length:", len(html))
        # Find all PDF links on the page
        pdf_links = re.findall(r'href=["\']([^"\']+\.pdf.*?)["\']', html, re.IGNORECASE)
        print("Found PDF links:", len(pdf_links))
        for link in pdf_links:
            if "ayush" in link.lower() or "guideline" in link.lower():
                print(" -> AYUSH/Guideline PDF link:", link)
            else:
                print(" -> Other PDF link:", link)
except Exception as e:
    print("Error:", e)
