"""
Compare Whisper models (tiny, base, small, medium) on Telugu and Kannada audio
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ip_sakti.services.transcription import validate_script_consistency
import time
import tempfile
from gtts import gTTS
import whisper

TEST_CASES = [
    ("te", "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"),
    ("kn", "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?")
]

MODELS = ["tiny", "base", "small"]

for lang, text in TEST_CASES:
    print(f"\n==================================================")
    print(f"TESTING LANGUAGE: {lang.upper()}")
    print(f"Target Text: {text}")

    tts = gTTS(text=text, lang=lang, slow=False)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tts.save(tmp.name)
    tmp_path = tmp.name
    tmp.close()

    for m_name in MODELS:
        print(f"\n--- Model: '{m_name}' (lang='{lang}') ---")
        t0 = time.time()
        try:
            model = whisper.load_model(m_name)
            res = model.transcribe(
                tmp_path,
                fp16=False,
                task="transcribe",
                language=lang,
                temperature=0.0,
                condition_on_previous_text=False
            )
            elapsed = time.time() - t0
            raw_text = res.get("text", "").strip()
            script_ok = validate_script_consistency(raw_text, lang)
            devanagari = sum(1 for c in raw_text if '\u0900' <= c <= '\u097f')
            telugu = sum(1 for c in raw_text if '\u0c00' <= c <= '\u0c7f')
            kannada = sum(1 for c in raw_text if '\u0c80' <= c <= '\u0cff')
            arabic = sum(1 for c in raw_text if '\u0600' <= c <= '\u06ff')

            print(f"Time: {elapsed:.2f}s | Script Valid: {script_ok}")
            print(f"RAW TRANSCRIPT: {raw_text!r}")
            print(f"Counts -> Telugu: {telugu}, Kannada: {kannada}, Devanagari: {devanagari}, Arabic: {arabic}")
        except Exception as err:
            print(f"Error loading/running {m_name}: {err}")

    os.remove(tmp_path)
