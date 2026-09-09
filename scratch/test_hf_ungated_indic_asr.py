"""
Check ungated ASR models for Telugu & Kannada on HuggingFace
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from huggingface_hub import HfApi

api = HfApi()

print("=== SEARCHING UNGATED TELUGU & KANNADA ASR REPOS ===")

try:
    models_te = api.list_models(filter="audio-to-audio", search="telugu", limit=10)
    print("\nTelugu ASR Models Found:")
    for m in models_te:
        print(f" - {m.id}")
except Exception as e:
    print(f"Telugu search error: {e}")

try:
    models_te_stt = api.list_models(filter="automatic-speech-recognition", search="telugu", limit=10)
    print("\nTelugu Automatic Speech Recognition Models Found:")
    for m in models_te_stt:
        print(f" - {m.id}")
except Exception as e:
    print(f"Telugu ASR search error: {e}")

try:
    models_kn_stt = api.list_models(filter="automatic-speech-recognition", search="kannada", limit=10)
    print("\nKannada Automatic Speech Recognition Models Found:")
    for m in models_kn_stt:
        print(f" - {m.id}")
except Exception as e:
    print(f"Kannada ASR search error: {e}")

