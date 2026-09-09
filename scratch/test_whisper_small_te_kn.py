"""
Test Whisper 'small' model on Telugu and Kannada audio with QueryTranslator
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ip_sakti.services.transcription import get_query_translator, validate_script_consistency
import time
import tempfile
from gtts import gTTS
import whisper

model_small = whisper.load_model("small")

TEST_CASES = [
    ("te", "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"),
    ("kn", "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?")
]

for lang, text in TEST_CASES:
    print(f"\n==================================================")
    print(f"Testing Language: {lang.upper()}")
    print(f"Original Text: {text}")

    tts = gTTS(text=text, lang=lang, slow=False)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tts.save(tmp.name)
    tmp_path = tmp.name
    tmp.close()

    t0 = time.time()
    res = model_small.transcribe(
        tmp_path,
        fp16=False,
        task="transcribe",
        language=lang,
        temperature=0.0,
        condition_on_previous_text=False,
        no_speech_threshold=0.6
    )
    elapsed = time.time() - t0

    raw_text = res.get("text", "").strip()
    print(f"Time Taken: {elapsed:.2f}s")
    print(f"RAW TRANSCRIPT: {raw_text!r}")

    script_ok = validate_script_consistency(raw_text, lang)
    print(f"Script Consistency Check ({lang}): {'PASSED' if script_ok else 'FAILED'}")

    if raw_text:
        try:
            qt = get_query_translator()
            translated = qt.translate_to_retrieval_language(raw_text, lang)
            print(f"QueryTranslator English Output: {translated.translated_text!r}")
        except Exception as err:
            print(f"Translation Error: {err}")

    os.remove(tmp_path)
