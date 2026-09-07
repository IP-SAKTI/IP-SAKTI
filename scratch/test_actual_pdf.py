import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://ipindia.gov.in/storage/uploads/docs-operator/335e2746-58c1-4b56-a1e5-cdd172a92a3c.pdf"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        print("URL:", url)
        print("Status:", resp.status)
        print("Content-Type:", resp.headers.get("Content-Type"))
        print("Content-Length:", resp.headers.get("Content-Length"))
except Exception as e:
    print("Error:", e)
