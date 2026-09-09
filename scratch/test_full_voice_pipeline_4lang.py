"""
Full End-to-End Test for 4-Language ASR Pipeline
Tests:
1. English (en) -> Whisper Base -> English
2. Hindi (hi) -> Whisper Base -> Devanagari script -> English translation
3. Telugu (te) -> Indic ASR (vasista22/whisper-telugu-base) -> Telugu script -> English translation
4. Kannada (kn) -> Indic ASR (vasista22/whisper-kannada-base) -> Kannada script -> English translation
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import time
import tempfile
from gtts import gTTS
from ip_sakti.services.transcription import transcribe_audio_bytes

def main():
    print("=== TESTING FULL 4-LANGUAGE ASR PIPELINE ===")

    test_cases = [
        ("en", "What permissions are required to manufacture an Ayurvedic medicine?"),
        ("hi", "आयुर्वेदिक दवा बनाने के लिए क्या लाइसेंस चाहिए?"),
        ("te", "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"),
        ("kn", "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?"),
    ]

    for lang, text in test_cases:
        print(f"\n" + "=" * 50)
        print(f"--- TESTING LANGUAGE: {lang.upper()} ---")
        print(f"Input text for gTTS: {text}")

        tts = gTTS(text=text, lang=lang, slow=False)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tts.save(tmp.name)
        tmp_path = tmp.name
        tmp.close()

        try:
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()

            t0 = time.time()
            res = transcribe_audio_bytes(
                audio_bytes=audio_bytes,
                filename="speech.mp3",
                content_type="audio/mp3",
                target_lang=lang
            )
            elapsed = time.time() - t0

            print(f"Inference Time: {elapsed:.2f}s")
            print(f"Result Language: {res.get('language')}")
            print(f"Raw Transcript: {res.get('transcript')!r}")
            print(f"Translated Text: {res.get('translated_text')!r}")
            print(f"Error: {res.get('error')!r}")

            assert res.get("error") is None, f"Error occurred for {lang}: {res.get('error')}"
            assert res.get("transcript"), f"Transcript is empty for {lang}"
            assert res.get("translated_text"), f"Translation is empty for {lang}"

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    print("\n" + "=" * 50)
    print("=== ALL 4 LANGUAGES PASSED FULL ASR & TRANSLATION PIPELINE! ===")

if __name__ == "__main__":
    main()
