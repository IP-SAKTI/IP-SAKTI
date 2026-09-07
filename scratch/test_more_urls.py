import urllib.request
import urllib.error
import ssl

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
strict_ctx = ssl.create_default_context()
unverified_ctx = ssl._create_unverified_context()

more_urls = [
    "https://www.indiacode.nic.in/handle/123456789/2046?locale=en",
    "https://www.indiacode.nic.in/",
    "https://e-nba.nic.in/",
    "https://nbaindia.org/",
    "http://nbaindia.org/",
    "https://ayush.gov.in/",
    "https://www.ayush.gov.in/",
    "https://pcimh.gov.in/",
    "https://ccras.nic.in/",
    "https://www.wipo.int/en/web/traditional-knowledge"
]

def test_url(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10, context=strict_ctx) as response:
            print(f"[OK] {url} -> Status {response.status}, Final: {response.url}")
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {url} -> Final: {e.url}")
    except urllib.error.URLError as e:
        if isinstance(e.reason, ssl.SSLError):
            try:
                with urllib.request.urlopen(req, timeout=10, context=unverified_ctx) as response:
                    print(f"[SSL_UNVERIFIED OK] {url} -> Status {response.status}, Final: {response.url}")
            except Exception as u_e:
                print(f"[SSL_UNVERIFIED FAIL] {url} -> {u_e}")
        else:
            print(f"[URL ERROR] {url} -> {e.reason}")
    except Exception as e:
        print(f"[EXC] {url} -> {e}")

if __name__ == "__main__":
    for u in more_urls:
        test_url(u)
