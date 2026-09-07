import urllib.request
import json

url = "http://127.0.0.1:8000/document/ip_india_patents_act_3p?format=json"
req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        print("API Response for ip_india_patents_act_3p:")
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error querying API: {e}")
