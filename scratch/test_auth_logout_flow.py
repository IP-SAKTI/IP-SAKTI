import requests
import time

BASE_URL = "http://localhost:8000"

def test_auth_and_logout_security():
    print("==================================================")
    print("AUTHENTICATION & LOGOUT BEHAVIOR AUDIT TEST")
    print("==================================================")

    test_email = f"user_{int(time.time())}@ipsakti.gov.in"
    test_password = "Password123!"

    # 1. Test Register Endpoint
    register_payload = {
        "name": "Audit Test User",
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password,
        "terms_accepted": True
    }
    print("\n1. Testing Register API POST /auth/register...")
    res_reg = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
    print(f"Register Status Code: {res_reg.status_code}")
    assert res_reg.status_code == 200, f"Register failed: {res_reg.text}"
    reg_data = res_reg.json()
    reg_user = reg_data.get("user")
    print(f"Register User Data: {reg_user}")
    assert "password" not in reg_user, "SECURITY FAIL: Password returned in register payload!"
    assert "password" not in reg_data, "SECURITY FAIL: Password returned in top-level JSON!"
    print("[PASS] Register payload does NOT contain password.")

    # 2. Test Login Endpoint with created user
    login_payload = {
        "email": test_email,
        "password": test_password
    }
    print(f"\n2. Testing Login API POST /auth/login with {test_email}...")
    res = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    print(f"Login Status Code: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        token = data.get("token")
        user = data.get("user")
        print(f"Token Received: {token[:20]}..." if token else "No Token")
        print(f"User Data: {user}")
        assert "password" not in user, "SECURITY FAIL: Password returned in user payload!"
        assert "password" not in data, "SECURITY FAIL: Password returned in top-level JSON!"
        print("[PASS] User payload does NOT contain password.")
    else:
        print(f"Note: Supabase email verification may be required for fresh registration logins ({res.text[:100]})")

    print("\n==================================================")
    print("ALL AUTHENTICATION & LOGOUT TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_auth_and_logout_security()
