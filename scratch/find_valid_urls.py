import urllib.request
import urllib.error
import ssl
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
strict_ctx = ssl.create_default_context()
unverified_ctx = ssl._create_unverified_context()

candidate_urls = {
    "ip_india_patents_act_3p": [
        "https://ipindia.gov.in/acts/patent-act-1970/section-3",
        "https://ipindia.gov.in/resource/patents-resources-act",
        "https://ipindia.gov.in/patents-act-1970.htm"
    ],
    "ip_india_tk_guidelines": [
        "https://ipindia.gov.in/resource/patents-resources-guidelines",
        "https://ipindia.gov.in/guidelines-for-examination.htm",
        "https://ipindia.gov.in/writereaddata/Portal/IPOGuidelinesManuals/1_38_1_4_guidelines-for-examination-of-patent-applications-traditional-knowledge.pdf",
        "https://ipindia.gov.in/storage/uploads/docs-operator/1_38_1_4_guidelines-for-examination-of-patent-applications-traditional-knowledge.pdf"
    ],
    "ayush_rule_158b": [
        "https://ayush.gov.in/pages/rules-and-regulations",
        "https://ayush.gov.in/",
        "https://cdsco.gov.in/opencms/opencms/en/Acts-and-rules/Drugs-Rules/"
    ],
    "ayush_form_24d": [
        "https://ayush.gov.in/pages/acts-rules-guidelines",
        "https://ayush.gov.in/",
        "https://cdsco.gov.in/opencms/opencms/en/Acts-and-rules/Drugs-Rules/"
    ],
    "biodiversity_act_2002": [
        "https://www.indiacode.nic.in/handle/123456789/2046?sam_handle=123456789/1362",
        "https://www.indiacode.nic.in/show-data?actid=AC_CEN_3_20_00003_200318_1517807324026",
        "https://nbaindia.org/content/19/16/1/act.html",
        "https://nbaindia.org/act/"
    ],
    "nba_abs_regulations_2014": [
        "https://nbaindia.org/content/683/61/1/rulesguidelines.html",
        "https://nbaindia.org/text/pdf/ABS_Regulations_2014.pdf",
        "https://nbaindia.org/uploaded/pdf/ABS_Regulations_2014.pdf",
        "https://nbaindia.org/"
    ],
    "tkdl_wipo_policy": [
        "https://www.wipo.int/tk/en/",
        "https://www.wipo.int/tk/en/databases/",
        "https://www.tkdl.res.in/",
        "https://www.wipo.int/tk/en/indigenous/"
    ],
    "ccras_ayush_pharmacopoeia": [
        "https://ccras.nic.in/",
        "https://pcimh.gov.in/",
        "https://pcimh.gov.in/index1.php?lang=1&level=1&sublinkid=72&lid=71",
        "https://ccras.nic.in/content/publications"
    ]
}

def test_url(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10, context=strict_ctx) as response:
            return {"url": url, "status": response.status, "ssl": True, "final": response.url}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "ssl": True, "final": e.url, "error": str(e)}
    except urllib.error.URLError as e:
        if isinstance(e.reason, ssl.SSLError):
            try:
                with urllib.request.urlopen(req, timeout=10, context=unverified_ctx) as response:
                    return {"url": url, "status": response.status, "ssl": False, "final": response.url}
            except Exception as u_e:
                return {"url": url, "status": None, "ssl": False, "error": str(u_e)}
        return {"url": url, "status": None, "ssl": False, "error": str(e.reason)}
    except Exception as e:
        return {"url": url, "status": None, "ssl": False, "error": str(e)}

def main():
    results = {}
    for key, urls in candidate_urls.items():
        print(f"=== Testing candidates for {key} ===")
        results[key] = []
        for url in urls:
            res = test_url(url)
            results[key].append(res)
            print(f"URL: {url} -> SSL: {res['ssl']}, Status: {res['status']}, Final: {res.get('final')}, Error: {res.get('error')}")
        print()

if __name__ == "__main__":
    main()
