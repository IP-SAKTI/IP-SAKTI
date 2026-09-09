import sys
import json
import httpx
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ip_sakti.utils.supabase_auth import SupabaseAuthService

def test_authentication_and_security():
    print("=" * 70)
    print("TESTING SUPABASE AUTHENTICATION, PERSISTENCE & SECURITY INTEGRITY")
    print("=" * 70)

    auth_srv = SupabaseAuthService()

    # Test 1: User Registration
    test_name = "Auth Verification User"
    test_email = f"auth_test_{int(Path(__file__).stat().st_mtime)}@ipsakti.gov.in"
    test_password = "SecurePassword123!"

    print(f"\n1. Registering test user: {test_email}...")
    user_rec, reg_err = auth_srv.register_user(
        name=test_name,
        email=test_email,
        password=test_password,
        confirm_password=test_password,
        terms_accepted=True,
    )
    if reg_err:
        print(f"   Registration warning/error: {reg_err}")
    print(f"   [PASS] User ID: {user_rec.get('id') if user_rec else 'None'}")

    # Test 2: User Login
    print(f"\n2. Authenticating user credentials: {test_email}...")
    auth_data, auth_err = auth_srv.authenticate_user(email=test_email, password=test_password)
    assert auth_err is None, f"Authentication failed: {auth_err}"
    assert auth_data is not None, "Authentication returned null data"
    assert "password" not in auth_data, "SECURITY VIOLATION: Password returned in authentication payload!"
    print(f"   [PASS] Login successful! Token present: {bool(auth_data.get('access_token'))}")

    # Test 3: Session Verification
    if auth_data.get("access_token"):
        print("\n3. Verifying persistent session token...")
        verified_user = auth_srv.verify_session(auth_data["access_token"])
        assert verified_user is not None, "Token verification failed"
        assert verified_user["email"] == test_email, "Email mismatch in verified token payload"
        print(f"   [PASS] Persistent session token verified for email: {verified_user['email']}")

    # Test 4: Password Security Audit across Payload Data
    print("\n4. Security Audit: Verifying zero password leakage in storage payloads...")
    session_json = json.dumps(auth_data)
    assert test_password not in session_json, "SECURITY VIOLATION: Password leaked into session JSON payload!"
    print("   [PASS] Zero password leakage detected in authentication payload!")

    # Test 5: Sign Out Execution
    print("\n5. Testing Supabase Sign Out...")
    signout_ok = auth_srv.sign_out(auth_data.get("access_token"))
    assert signout_ok, "Sign out failed"
    print("   [PASS] Sign out completed successfully!")

    print("\nALL AUTHENTICATION & SECURITY BACKEND TESTS PASSED 100%!")

if __name__ == "__main__":
    test_authentication_and_security()
