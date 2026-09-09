"""
Test loading AI4Bharat IndicConformer models for Telugu & Kannada
ai4bharat/indicconformer_stt_te_hybrid_ctc_rnnt_large
ai4bharat/indicconformer_stt_kn_hybrid_ctc_rnnt_large
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("=== AI4BHARAT INDICCONFORMER LOAD DIAGNOSTIC ===")

# Test 1: Try importing AutoModelForCTC / AutoModel from transformers
try:
    from transformers import AutoModelForCTC, AutoProcessor
    print("Transformers AutoModelForCTC and AutoProcessor imported successfully.")
except Exception as e:
    print(f"Transformers import error: {e}")

# Test 2: Try downloading/inspecting config of ai4bharat/indicconformer_stt_te_hybrid_ctc_rnnt_large
try:
    from huggingface_hub import hf_hub_download
    config_path = hf_hub_download(repo_id="ai4bharat/indicconformer_stt_te_hybrid_ctc_rnnt_large", filename="config.json")
    print(f"Downloaded config.json for Telugu IndicConformer: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        print("Config snippet:", f.read()[:300])
except Exception as e:
    print(f"Hugging Face hub download error: {e}")

# Test 3: Attempt AutoModelForCTC load
try:
    print("\nAttempting to load model via AutoModelForCTC.from_pretrained('ai4bharat/indicconformer_stt_te_hybrid_ctc_rnnt_large')...")
    model = AutoModelForCTC.from_pretrained("ai4bharat/indicconformer_stt_te_hybrid_ctc_rnnt_large")
    print("AutoModelForCTC loaded successfully!")
except Exception as e:
    print(f"AutoModelForCTC load failed: {e}")

