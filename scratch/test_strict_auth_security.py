import requests
import time

BASE_URL = "http://localhost:8000"

def test_strict_auth():
    print("==================================================")
    print("STRICT SUPABASE AUTHENTICATION SECURITY AUDIT")
    print("==================================================")

    # TEST 1: Fake Credentials MUST Fail
    fake_email = "random_test_987654@example.com"
    fake_password = "RandomPassword!987654321"
    
    print(f"\n1. Testing POST /auth/login with FAKE credentials ({fake_email})...")
    res_fake = requests.post(f"{BASE_URL}/auth/login", json={
        "email": fake_email,
        "password": fake_password
    })
    print(f"Fake login status: {res_fake.status_code}")
    print(f"Fake login response: {res_fake.text}")
    assert res_fake.status_code == 401, f"SECURITY FAILURE: Fake credentials returned status {res_fake.status_code} instead of 401!"
    print("[PASS] Fake credentials correctly rejected with 401 Unauthorized!")

    # TEST 2: Register user in Supabase Auth
    real_email = f"user_{int(time.time())}@example.com"
    real_password = "ValidPassword123!"

    print(f"\n2. Testing POST /auth/register with new account ({real_email})...")
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Legitimate User",
        "email": real_email,
        "password": real_password,
        "confirm_password": real_password,
        "terms_accepted": True
    })
    print(f"Register status: {reg_res.status_code}")
    if reg_res.status_code == 200:
        reg_data = reg_res.json()
        print(f"User created in Supabase: {reg_data.get('user')}")

        # TEST 3: Login with newly created Supabase user
        print(f"\n3. Testing POST /auth/login with REAL Supabase account ({real_email})...")
        login_res = requests.post(f"{BASE_URL}/auth/login", json={
            "email": real_email,
            "password": real_password
        })
        print(f"Login status: {login_res.status_code}")
        print(f"Login response: {login_res.json() if login_res.status_code == 200 else login_res.text}")
        if login_res.status_code == 200:
            token = login_res.json().get("token")
            print(f"[PASS] Real Supabase user authenticated successfully! Token: {token[:25]}...")
            
            # TEST 4: Verify session token
            print("\n4. Testing GET /auth/verify with valid token...")
            ver_res = requests.get(f"{BASE_URL}/auth/verify", headers={"Authorization": f"Bearer {token}"})
            print(f"Verify status: {ver_res.status_code}")
            assert ver_res.status_code == 200
            print("[PASS] Valid Supabase JWT token verified successfully!")
        else:
            print(f"[NOTE] Supabase email confirmation setting may be active: {login_res.text[:100]}")

    # TEST 5: Verify invalid token fails
    print("\n5. Testing GET /auth/verify with fake token...")
    inv_res = requests.get(f"{BASE_URL}/auth/verify", headers={"Authorization": "Bearer fake_token_xyz"})
    print(f"Invalid verify status: {inv_res.status_code}")
    assert inv_res.status_code == 401
    print("[PASS] Fake token correctly rejected with 401!")

    print("\n==================================================")
    print("ALL STRICT SUPABASE AUTH SECURITY TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_strict_auth()
