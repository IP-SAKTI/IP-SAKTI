"""
Test script for NLLB-200 translation of Hindi, Telugu, Kannada to English
"""
import time
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "facebook/nllb-200-distilled-600M"

LANGUAGE_MAP = {
    "hi": "hin_Deva",
    "te": "tel_Telu",
    "kn": "kan_Knda",
    "en": "eng_Latn",
}

def main():
    print("Loading tokenizer and model...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    print(f"Model loaded in {time.time() - t0:.2f} seconds.")

    test_queries = [
        ("hi", "आयुर्वेदिक दवा बनाने के लिए क्या लाइसेंस चाहिए?"),
        ("te", "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"),
        ("kn", "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?"),
        ("en", "What permissions are required to manufacture an Ayurvedic medicine?")
    ]

    for lang_code, text in test_queries:
        if lang_code == "en":
            print(f"\n[{lang_code.upper()}] Input: {text}")
            print(f"[{lang_code.upper()}] Translation: {text}")
            continue

        src_lang = LANGUAGE_MAP.get(lang_code, "hin_Deva")
        tgt_lang = "eng_Latn"

        inputs = tokenizer(text, return_tensors="pt")
        forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang)

        # Set source language token
        tokenizer.src_lang = src_lang
        inputs = tokenizer(text, return_tensors="pt")

        t1 = time.time()
        translated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=128
        )
        translated_text = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        print(f"\n[{lang_code.upper()}] Input: {text}")
        print(f"[{lang_code.upper()}] Translated ({time.time() - t1:.2f}s): {translated_text}")

if __name__ == "__main__":
    main()
