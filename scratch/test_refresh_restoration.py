"""
scratch/test_refresh_restoration.py — Test research workspace refresh restoration & database message metadata.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def main():
    print("==================================================")
    print("TESTING REFRESH RESTORATION & DATABASE INTEGRITY")
    print("==================================================")

    # 1. Register test user
    timestamp = int(time.time())
    email = f"user_refresh_{timestamp}@gmail.com"
    password = "TestPassword123!"

    reg = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Refresh User",
        "email": email,
        "password": password,
        "confirm_password": password,
        "terms_accepted": True
    })
    assert reg.status_code in (200, 201), f"Registration failed: {reg.text}"
    user_data = reg.json()["user"]
    user_id = user_data["id"]
    token = reg.json().get("token") or f"token-{user_id}"
    print(f"[PASS] Registered test user: id={user_id}")

    # 2. Run real research query via /query
    headers = {"Authorization": f"Bearer {token}"}
    q_text = "Is turmeric + neem patentable in India?"
    query_resp = requests.post(f"{BASE_URL}/query", headers=headers, json={"raw_query": q_text})
    assert query_resp.status_code == 200, f"Query failed: {query_resp.text}"
    resp_data = query_resp.json()
    conv_id = resp_data.get("query_id") or f"conv-ref-{timestamp}"
    print(f"[PASS] Query executed successfully: query_id={conv_id}")

    # 3. Save conversation to Supabase PostgreSQL via /history
    save_resp = requests.post(f"{BASE_URL}/history", headers=headers, json={
        "id": conv_id,
        "title": "Turmeric & Neem Patentability",
        "query": q_text,
        "user_id": user_id,
        "response": resp_data
    })
    assert save_resp.status_code == 200, f"Save history failed: {save_resp.text}"
    print(f"[PASS] Saved conversation {conv_id} to Supabase PostgreSQL.")

    # 4. Simulate Page Refresh: fetch GET /history/{conv_id}
    detail_resp = requests.get(f"{BASE_URL}/history/{conv_id}?user_id={user_id}", headers=headers)
    assert detail_resp.status_code == 200, f"Detail fetch failed: {detail_resp.text}"
    detail_data = detail_resp.json()
    assert detail_data is not None, "Detail data is null"
    assert "messages" in detail_data and len(detail_data["messages"]) >= 2, f"Invalid message history: {detail_data}"

    user_msg = next((m for m in detail_data["messages"] if m["role"] == "user"), None)
    assistant_msg = next((m for m in detail_data["messages"] if m["role"] == "assistant"), None)

    assert user_msg is not None, "Missing user message"
    assert assistant_msg is not None, "Missing assistant message"
    assert user_msg["content"] == q_text, "User message content mismatch"
    assert assistant_msg["metadata"] is not None and "response" in assistant_msg["metadata"], "Missing assistant response metadata"

    restored_resp = assistant_msg["metadata"]["response"]
    assert restored_resp["answer"] == resp_data["answer"], "Restored answer mismatch"
    assert restored_resp["confidence"] == resp_data["confidence"], "Restored confidence mismatch"
    assert len(restored_resp["evidence"]) == len(resp_data["evidence"]), "Restored evidence length mismatch"

    print("[PASS] Successfully fetched GET /history/{id} on refresh simulation.")
    print(f"[PASS] Restored Question: {user_msg['content']}")
    print(f"[PASS] Restored Answer length: {len(restored_resp['answer'])} chars")
    print(f"[PASS] Restored Evidence count: {len(restored_resp['evidence'])}")

    # 5. User Isolation Check
    user_b_id = f"usr-other-{timestamp}"
    detail_unauth = requests.get(f"{BASE_URL}/history/{conv_id}?user_id={user_b_id}")
    assert detail_unauth.status_code in (403, 404), f"User isolation failed: HTTP {detail_unauth.status_code}"
    print("[PASS] User isolation check passed: Unauthorized access to conversation rejected with HTTP 403/404.")

    print("ALL REFRESH RESTORATION TESTS PASSED 100%!")

if __name__ == "__main__":
    main()
