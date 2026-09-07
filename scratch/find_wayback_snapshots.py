import json
import urllib.request
import urllib.error

CONFIG_PATH = "config/sources.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    sources = json.load(f)

print(f"Checking Wayback Machine snapshots for {len(sources)} sources...\n")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) IP-SAKTI-Auditor/1.0'}

test_urls = {
    "ip_india_patents_act_3p": [
        "https://ipindia.gov.in/acts/patent-act-1970/section-3",
        "https://www.ipindia.gov.in/patents.htm",
        "https://ipindia.gov.in/patents.htm"
    ],
    "ip_india_tk_guidelines": [
        "https://ipindia.gov.in/resource/patents-resources-guidelines",
        "https://www.ipindia.gov.in/guidelines-for-examination-of-patent-applications.htm"
    ],
    "ayush_rule_158b": [
        "https://www.ayush.gov.in/docs/asu-l-rules.pdf",
        "https://cdsco.gov.in/opencms/opencms/en/Acts-and-rules/Drugs-Rules/"
    ],
    "ayush_form_24d": [
        "https://www.ayush.gov.in/regulatory-framework",
        "https://ayush.gov.in/"
    ],
    "biodiversity_act_2002": [
        "https://www.indiacode.nic.in/handle/123456789/2046",
        "https://nbaindia.org/act/"
    ],
    "nba_abs_regulations_2014": [
        "https://nbaindia.org/uploaded/pdf/ABS_Regulations_2014.pdf",
        "http://nbaindia.org/uploaded/pdf/ABS_Regulations_2014.pdf"
    ],
    "tkdl_wipo_policy": [
        "https://www.wipo.int/tk/en/databases/tkdl.html",
        "https://www.wipo.int/tk/en/"
    ],
    "ccras_ayush_pharmacopoeia": [
        "https://www.ccras.nic.in/content/ayurvedic-pharmacopoeia-india",
        "https://ccras.nic.in/"
    ],
    "cdsco_drugs_rules_1945": [
        "https://cdsco.gov.in/opencms/opencms/en/Acts-and-rules/Drugs-Rules/"
    ],
    "ip_india_ayush_guidelines_2025": [
        "https://ipindia.gov.in/resource/patents-resources-guidelines",
        "https://www.ipindia.gov.in/writereaddata/Portal/IPOGuidelinesManuals/Guidelines_for_Examination_of_Ayush_Related_Inventions.pdf"
    ]
}

found_snapshots = {}

for sid, url_list in test_urls.items():
    print(f"=== {sid} ===")
    found = False
    for url in url_list:
        api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(url)}"
        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                snapshots = data.get("archived_snapshots", {})
                closest = snapshots.get("closest")
                if closest and closest.get("available") and closest.get("url"):
                    snapshot_url = closest.get("url")
                    print(f"  [FOUND] Target URL: {url}")
                    print(f"          Snapshot URL: {snapshot_url}")
                    print(f"          Status: {closest.get('status')}, Timestamp: {closest.get('timestamp')}")
                    found_snapshots[sid] = snapshot_url
                    found = True
                    break
        except Exception as e:
            print(f"  [ERROR] Checking {url}: {e}")
    if not found:
        print("  [NOT FOUND] No available Wayback snapshot.")
    print("-" * 60)

print("\n=== SUMMARY OF VERIFIED SNAPSHOTS ===")
print(json.dumps(found_snapshots, indent=2))
