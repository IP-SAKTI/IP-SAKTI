"""
scratch/audit_env_gemini.py

Safely audit environment variables and verify Gemini API key authentication
WITHOUT printing or logging sensitive keys or tokens.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env explicitly
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

gemini_key = os.getenv("GEMINI_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
gemini_tts_model = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")

print(f"GEMINI_API_KEY: {'PRESENT' if gemini_key else 'MISSING'}")
print(f"GOOGLE_API_KEY: {'PRESENT' if google_key else 'MISSING'}")
print(f"TEXT MODEL: {gemini_model}")
print(f"TTS MODEL: {gemini_tts_model}")

# Test minimal authenticated Gemini text request using configured GEMINI_API_KEY
import google.generativeai as genai

active_key = gemini_key or google_key

if not active_key:
    print("TEST RESULT: FAILED - No API Key Found in .env")
    sys.exit(1)

genai.configure(api_key=active_key)

print("\nListing available models for this key:")
try:
    available = []
    all_m = genai.list_models()
    for m in all_m:
        methods = getattr(m, "supported_generation_methods", []) or []
        if "generateContent" in methods:
            clean_name = m.name.replace("models/", "")
            available.append(clean_name)
            print(f" - {clean_name}")
except Exception as e:
    print(f"Error listing models: {e}")

# Try minimal text generation request
target_text_models = [gemini_model, "gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash", "gemini-flash-latest"]
success = False

for m_candidate in target_text_models:
    try:
        print(f"\nTesting text generation on candidate model: '{m_candidate}'...")
        model = genai.GenerativeModel(model_name=m_candidate)
        res = model.generate_content("Reply with exactly: GEMINI_OK")
        if res and res.text:
            out_text = res.text.strip()
            print(f"SUCCESS on model '{m_candidate}'! Output: {out_text!r}")
            success = True
            break
    except Exception as exc:
        print(f"Candidate model '{m_candidate}' failed: {exc}")

if success:
    print("\nOVERALL GEMINI TEST RESULT: SUCCESS (GEMINI_OK)")
else:
    print("\nOVERALL GEMINI TEST RESULT: FAILED")
