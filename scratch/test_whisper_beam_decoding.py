"""
Test Whisper decoding settings (beam_size, best_of, temperature) for Telugu and Kannada
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ip_sakti.services.transcription import get_whisper_model, validate_script_consistency
import tempfile
from gtts import gTTS
import whisper

model = get_whisper_model("base")

TEST_CASES = [
    ("te", "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"),
    ("kn", "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?")
]

DECODING_CONFIGS = [
    {"name": "Greedy Default", "kwargs": {"temperature": 0.0, "condition_on_previous_text": False}},
    {"name": "Beam Search (beam_size=5)", "kwargs": {"beam_size": 5, "best_of": 5, "condition_on_previous_text": False}},
    {"name": "Low Temp (temperature=0.2)", "kwargs": {"temperature": 0.2, "condition_on_previous_text": False}},
    {"name": "With Previous Context", "kwargs": {"temperature": 0.0, "condition_on_previous_text": True}},
]

for lang, text in TEST_CASES:
    print(f"\n==================================================")
    print(f"LANGUAGE: {lang.upper()}")
    print(f"Target Text: {text}")

    tts = gTTS(text=text, lang=lang, slow=False)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tts.save(tmp.name)
    tmp_path = tmp.name
    tmp.close()

    for cfg in DECODING_CONFIGS:
        print(f"\n--- Testing Config: {cfg['name']} ---")
        try:
            res = model.transcribe(
                tmp_path,
                fp16=False,
                task="transcribe",
                language=lang,
                **cfg["kwargs"]
            )
            raw_text = res.get("text", "").strip()
            print(f"RAW TRANSCRIPT: {raw_text!r}")
            script_ok = validate_script_consistency(raw_text, lang)
            print(f"Script Validation ({lang}): {'PASSED' if script_ok else 'FAILED'}")
        except Exception as err:
            print(f"Error: {err}")

    os.remove(tmp_path)
