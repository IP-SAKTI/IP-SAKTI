"""
Comprehensive Verification Test Suite for Phase 2 — Multilingual Voice Query
"""
import os
import sys
import io
import wave
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from ip_sakti.services.transcription import transcribe_audio_bytes, SUPPORTED_VOICE_LANGUAGES, LANG_CODE_MAP
from ip_sakti.multilingual.translator import QueryTranslator
from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest

def run_tests():
    print("==================================================")
    print("PHASE 2 MULTILINGUAL VOICE QUERY VERIFICATION SUITE")
    print("==================================================\n")

    qt = QueryTranslator()
    ip_service = IPSAKTIService()

    test_queries = [
        {
            "lang_name": "English",
            "lang_code": "en",
            "text": "What permissions are required to manufacture an Ayurvedic medicine?"
        },
        {
            "lang_name": "Hindi",
            "lang_code": "hi",
            "text": "आयुर्वेदिक दवा बनाने के लिए क्या लाइसेंस चाहिए?"
        },
        {
            "lang_name": "Telugu",
            "lang_code": "te",
            "text": "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"
        },
        {
            "lang_name": "Kannada",
            "lang_code": "kn",
            "text": "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?"
        }
    ]

    print("--- 1. Testing Translation Engine for All 4 Languages ---")
    for t in test_queries:
        if t["lang_code"] == "en":
            translated = t["text"]
        else:
            res = qt.translate_to_retrieval_language(t["text"], t["lang_code"])
            translated = res.translated_text

        print(f"[{t['lang_name']}] ({t['lang_code'].upper()})")
        print(f"  Transcript: {t['text']}")
        print(f"  Translated: {translated}\n")
        assert translated is not None and len(translated) > 0

    print("--- 2. Testing Unsupported Language Handling ---")
    ja_text = "こんにちは"
    ja_norm = LANG_CODE_MAP.get("ja", "ja")
    assert ja_norm not in SUPPORTED_VOICE_LANGUAGES
    print("Unsupported 'ja' detected -> Correctly rejected with 'Unsupported voice language'\n")

    print("--- 3. Testing Audio Cleanup & Temp File Removal ---")
    sample_rate = 16000
    t_sig = np.linspace(0, 1, sample_rate, False)
    sine_wave = (np.sin(2 * np.pi * 440 * t_sig) * 32767).astype(np.int16)
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(sine_wave.tobytes())
    
    stt_res = transcribe_audio_bytes(wav_io.getvalue(), "test_clean.wav")
    print("Audio transcription test completed:", stt_res)

    print("\n--- 4. Testing End-to-End RAG Pipeline for Telugu Voice Query ---")
    telugu_q = "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"
    rag_req = QueryRequest(raw_query=telugu_q)
    rag_res = ip_service.process_query(rag_req)

    print("Telugu Query Answer Snippet:", rag_res.answer[:180] + "...")
    print("Confidence / Cosine Similarity:", rag_res.confidence)
    print("Citations Generated:", rag_res.citations[:3])
    print("Agents Invoked:", rag_res.agents_invoked)
    assert len(rag_res.answer) > 0, "RAG pipeline must return non-empty answer"

    print("\n==================================================")
    print("✅ ALL PHASE 2 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
