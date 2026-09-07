import urllib.request

url = "http://localhost:8501/"
try:
    with urllib.request.urlopen(url, timeout=5) as resp:
        print(f"Streamlit UI is accessible on port 8501. Status: {resp.status}")
except Exception as e:
    print(f"Streamlit UI check failed on port 8501: {e}")
