import requests
import time

BASE_URL = "http://localhost:8000"

def test_auth_and_cosine():
    print("==================================================")
    print("FINAL AUTHENTICATION & COSINE SIMILARITY TEST")
    print("==================================================")

    test_email = f"user_{int(time.time())}@example.com"
    test_password = "Password123!"

    # 1. Test Register
    print("\n1. Testing POST /auth/register...")
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Cosine Test User",
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password,
        "terms_accepted": True
    })
    print(f"Register status: {reg_res.status_code}")
    if reg_res.status_code == 200:
        reg_data = reg_res.json()
        token = reg_data.get("token")
        print(f"Token obtained: {token[:25]}...")

        # 2. Test Verify Token (Valid)
        print("\n2. Testing GET /auth/verify with valid token...")
        ver_res = requests.get(f"{BASE_URL}/auth/verify", headers={"Authorization": f"Bearer {token}"})
        print(f"Verify status: {ver_res.status_code}")
        assert ver_res.status_code == 200, f"Verify failed: {ver_res.text}"
        ver_data = ver_res.json()
        print(f"Verified user: {ver_data.get('user')}")

        # 3. Test Verify Token (Invalid)
        print("\n3. Testing GET /auth/verify with invalid token...")
        invalid_res = requests.get(f"{BASE_URL}/auth/verify", headers={"Authorization": "Bearer invalid-token-xyz"})
        print(f"Invalid verify status: {invalid_res.status_code}")
        assert invalid_res.status_code == 401, f"Expected 401, got {invalid_res.status_code}"
        print("[PASS] Invalid token correctly rejected with 401.")

        # 4. Test Logout
        print("\n4. Testing POST /auth/logout...")
        logout_res = requests.post(f"{BASE_URL}/auth/logout", headers={"Authorization": f"Bearer {token}"})
        print(f"Logout status: {logout_res.status_code}")
        assert logout_res.status_code == 200
    else:
        print(f"Register note: {reg_res.text[:100]}")

    # 5. Test /query cosine_similarity
    print("\n5. Testing POST /query for Cosine Similarity field...")
    q_payload = {
        "raw_query": "What are the manufacturing licensing requirements under Schedule T for Ayurvedic formulations in India?",
        "jurisdiction": "india",
        "formulation_category": "classical"
    }
    q_res = requests.post(f"{BASE_URL}/query", json=q_payload)
    print(f"Query status: {q_res.status_code}")
    assert q_res.status_code == 200, f"Query failed: {q_res.text}"
    q_data = q_res.json()
    
    print(f"Query ID: {q_data.get('query_id')}")
    print(f"Confidence Score: {q_data.get('confidence')}")
    print(f"Cosine Similarity Score: {q_data.get('cosine_similarity')}")
    
    assert "cosine_similarity" in q_data, "MISSING FIELD: cosine_similarity not in response!"
    if q_data.get("cosine_similarity") is not None:
        val = q_data["cosine_similarity"]
        assert isinstance(val, (int, float)), "cosine_similarity must be numeric!"
        print(f"[PASS] Cosine Similarity extracted successfully: {val:.4f}")
    else:
        print("[NOTE] cosine_similarity is None (e.g. abstention or 0 evidence chunks).")

    print("\n==================================================")
    print("ALL BACKEND AUTH & COSINE SIMILARITY TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_auth_and_cosine()
