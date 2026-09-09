"""
scratch/debug_supabase_flow.py — Inspect auth.users and profiles in Supabase PostgreSQL.
"""

from ip_sakti.utils.supabase_client import SupabaseClient
import json

def main():
    client = SupabaseClient()
    print("Supabase Configured:", client.is_configured)
    print("Supabase URL:", client.url)

    # Query profiles table
    try:
        profiles = client.select(table="profiles", params={"select": "*"}, use_service_role=True)
        print(f"\n--- PROFILES IN SUPABASE ({len(profiles)}) ---")
        for p in profiles:
            print(f"ID: {p.get('id')} | DisplayName: {p.get('display_name')} | Email: {p.get('email')}")
    except Exception as exc:
        print("Failed to query profiles:", exc)

    # Query conversations table
    try:
        conv_rows = client.select(table="conversations", params={"select": "*", "order": "updated_at.desc"}, use_service_role=True)
        print(f"\n--- CONVERSATIONS IN SUPABASE ({len(conv_rows)}) ---")
        for r in conv_rows:
            print(f"ID: {r.get('id')} | UserID: {r.get('user_id')} | Title: {r.get('title')}")
    except Exception as exc:
        print("Failed to query conversations:", exc)

if __name__ == "__main__":
    main()
