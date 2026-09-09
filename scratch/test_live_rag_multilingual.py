"""
Live Integration Test Script for Multilingual RAG Queries (English, Hindi, Telugu, Kannada)
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_live_rag_queries():
    print("=== Testing Live RAG Pipeline for Multilingual Queries ===")

    test_cases = [
        {
            "lang": "English",
            "query": "What regulatory requirements should be considered before manufacturing and commercially selling an Ayurvedic formulation in India?"
        },
        {
            "lang": "Hindi",
            "query": "भारत में आयुर्वेदिक फॉर्मूलेशन के निर्माण और व्यावसायिक बिक्री के लिए क्या नियम हैं?"
        },
        {
            "lang": "Telugu",
            "query": "భారతదేశంలో ఆయుర్వేద మూలికా ఔషధ తయారీకి ఏ లైసెన్స్ మరియు అనుమతులు అవసరం?"
        },
        {
            "lang": "Kannada",
            "query": "ಭಾರತದಲ್ಲಿ ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಮತ್ತು ಮಾರಾಟ ಮಾಡಲು ಯಾವ ನಿಯಮಗಳು ಬೇಕು?"
        }
    ]

    for tc in test_cases:
        print(f"\n--- Testing {tc['lang']} Query ---")
        print("Query Text:", tc['query'])

        res = requests.post(
            f"{BASE_URL}/query",
            json={"raw_query": tc['query']}
        )

        assert res.status_code == 200, f"Failed with status {res.status_code}: {res.text}"
        data = res.json()

        print("HTTP Status:", res.status_code)
        print("AnswerSnippet:", data.get("answer", "")[:160] + "...")
        print("Citations:", data.get("citations", []))
        print("Agents Invoked:", data.get("agents_invoked", []))
        print("Cosine Similarity / Confidence:", data.get("confidence"))

        assert "answer" in data and len(data["answer"]) > 0, "Answer must not be empty"
        assert len(data.get("evidence", [])) > 0 or data.get("is_abstention"), "Evidence or safe abstention required"

    print("\nSUCCESS: All Live RAG Multilingual Query Tests Passed Error-Free!")

if __name__ == "__main__":
    test_live_rag_queries()
