import urllib.request
import ssl
import re
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://ipindia.gov.in/resource/patents-resources-guidelines"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    html = resp.read().decode("utf-8", errors="ignore")

soup = BeautifulSoup(html, "html.parser")
for a in soup.find_all("a", href=True):
    text = a.get_text(strip=True)
    parent_text = a.parent.get_text(strip=True) if a.parent else ""
    if "ayush" in text.lower() or "ayush" in parent_text.lower() or "traditional" in text.lower():
        print("Link text:", text)
        print("Parent text:", parent_text[:100])
        print("HREF:", a["href"])
        print("-" * 50)
