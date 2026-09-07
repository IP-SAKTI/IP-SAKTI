import urllib.request
import ssl
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
for tr in soup.find_all("tr"):
    text = tr.get_text(" | ", strip=True)
    a = tr.find("a", href=True)
    if a:
        print("Row:", text)
        print("HREF:", a["href"])
        print("=" * 60)
