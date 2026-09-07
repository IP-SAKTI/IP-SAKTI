import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://www.ipindia.gov.in/uploads/48750b1a-6e7e-481f-a6ff-ec5804cfdb78_Guidelines%20for%20Examination%20of%20Ayush%20Related%20Inventions.pdf",
    "https://ipindia.gov.in/uploads/48750b1a-6e7e-481f-a6ff-ec5804cfdb78_Guidelines%20for%20Examination%20of%20Ayush%20Related%20Inventions.pdf",
    "https://www.ipindia.gov.in/uploads/48750b1a-6e7e-481f-a6ff-ec5804cfdb78_Guidelines for Examination of Ayush Related Inventions.pdf",
    "https://ipindia.gov.in/uploads/48750b1a-6e7e-481f-a6ff-ec5804cfdb78_Guidelines for Examination of Ayush Related Inventions.pdf",
]

for url in urls:
    # urllib needs encoded url
    import urllib.parse
    parts = urllib.parse.urlsplit(url)
    encoded_path = urllib.parse.quote(parts.path)
    clean_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, parts.query, parts.fragment))
    req = urllib.request.Request(clean_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print(f"URL: {clean_url}")
            print(f"Status: {resp.status}, Content-Type: {resp.headers.get('Content-Type')}\n")
    except Exception as e:
        print(f"URL: {clean_url}")
        print(f"Error: {e}\n")
