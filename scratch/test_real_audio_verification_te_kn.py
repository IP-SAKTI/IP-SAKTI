"""
Real Audio Verification Script for Telugu, Kannada, Hindi, and English Speech Recognition
Tests real spoken audio for Telugu ("ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?")
and Kannada ("ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?")
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import tempfile
from gtts import gTTS
from ip_sakti.services.transcription import transcribe_audio_bytes, validate_script_consistency

TEST_CASES = [
    {
        "lang_code": "te",
        "text": "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?",
        "label": "Telugu"
    },
    {
        "lang_code": "kn",
        "text": "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?",
        "label": "Kannada"
    },
    {
        "lang_code": "hi",
        "text": "आयुर्वेदिक दवा बनाने के लिए कौन सी अनुमति चाहिए?",
        "label": "Hindi"
    },
    {
        "lang_code": "en",
        "text": "What permissions are required to manufacture Ayurvedic medicine?",
        "label": "English"
    }
]

def run_tests():
    print("=" * 60)
    print("REAL AUDIO VERIFICATION FOR TELUGU & KANNADA STT")
    print("=" * 60)

    for case in TEST_CASES:
        l_code = case["lang_code"]
        text = case["text"]
        label = case["label"]

        print(f"\n--- Testing {label} ({l_code.upper()}) ---")
        print(f"Target Spoken Sentence: {text}")

        # Generate audio using native TTS pronunciation
        tts = gTTS(text=text, lang=l_code, slow=False)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tts.save(tmp.name)
        tmp_path = tmp.name
        tmp.close()

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        t0 = time.time()
        res = transcribe_audio_bytes(audio_bytes, filename=f"test_{l_code}.mp3", target_lang=l_code)
        elapsed = time.time() - t0

        print(f"Time Taken: {elapsed:.2f}s")
        print(f"Returned Dict: {res}")

        # Validate script consistency
        script_ok = validate_script_consistency(res.get("transcript", ""), l_code)
        print(f"Script Consistency Check: {'PASSED' if script_ok else 'FAILED'}")

        os.remove(tmp_path)

if __name__ == "__main__":
    run_tests()
