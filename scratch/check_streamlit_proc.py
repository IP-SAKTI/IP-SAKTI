import urllib.request

url = "http://localhost:8501/"
try:
    with urllib.request.urlopen(url, timeout=3) as resp:
        print(f"Streamlit process is currently running on port 8501. Status: {resp.status}")
except Exception as e:
    print(f"Streamlit process check: {e}")
