"""
scratch/test_postgrest_uuid_behavior.py — Reproduce PostgREST 400 Bad Request on invalid UUID syntax.
"""

from ip_sakti.utils.supabase_client import SupabaseClient
from ip_sakti.utils.supabase_chat_storage import sanitize_uuid
import uuid

def main():
    client = SupabaseClient()
    if not client.is_configured:
        print("Supabase not configured.")
        return

    # Test 1: Query with valid UUID
    valid_uuid = "31b4b9b8-2eaf-4254-bbb6-dad9ade3221a"
    try:
        res1 = client.select(table="conversations", params={"user_id": f"eq.{valid_uuid}"}, use_service_role=True)
        print(f"[TEST 1] Query with valid UUID ({valid_uuid}) SUCCESS: returned {len(res1)} rows.")
    except Exception as exc:
        print(f"[TEST 1] Query with valid UUID FAILED: {exc}")

    # Test 2: Query with invalid non-UUID string
    invalid_uid = "usr-usera_1788953845"
    try:
        res2 = client.select(table="conversations", params={"user_id": f"eq.{invalid_uid}"}, use_service_role=True)
        print(f"[TEST 2] Query with invalid string ({invalid_uid}) SUCCESS: returned {len(res2)} rows.")
    except Exception as exc:
        print(f"[TEST 2] Query with invalid string FAILED (Expected PostgREST 400): {exc}")

if __name__ == "__main__":
    main()
