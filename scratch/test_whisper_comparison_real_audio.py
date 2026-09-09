"""
Real Audio Test Script for Whisper STT Model Comparison & Multilingual Diagnosis
Tests real spoken audio for Telugu, Hindi, Kannada, and English.
Compares Whisper 'tiny' vs 'base' models on Telugu audio.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import tempfile
from gtts import gTTS
import whisper
from ip_sakti.services.transcription import transcribe_audio_bytes, get_whisper_model

SENTENCES = {
    "te": "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?",
    "hi": "आयुर्वेदिक दवा बनाने के लिए कौन सी अनुमति चाहिए?",
    "kn": "ಆಯುರ್ವೇದ ಔಷಧಿಯನ್ನು ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?",
    "en": "What permissions are required to manufacture Ayurvedic medicine?"
}

def generate_audio_file(text: str, lang: str) -> str:
    """Generate audio file using gTTS."""
    tts = gTTS(text=text, lang=lang, slow=False)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tts.save(tmp.name)
    tmp.close()
    return tmp.name

def run_model_comparison_telugu():
    print("=" * 60)
    print("WHISPER MODEL COMPARISON ON REAL TELUGU AUDIO")
    print("Target Sentence: ", SENTENCES["te"])
    print("=" * 60)

    audio_path = generate_audio_file(SENTENCES["te"], "te")
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    print(f"Generated Audio File Size: {len(audio_bytes)} bytes\n")

    models_to_test = ["tiny", "base"]
    comparison_table = []

    for m_name in models_to_test:
        t0 = time.time()
        print(f"Loading Whisper '{m_name}' model...")
        model = whisper.load_model(m_name)
        
        # Audio language detection
        audio = whisper.load_audio(audio_path)
        audio_padded = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio_padded).to(model.device)
        _, probs = model.detect_language(mel)
        top_lang = max(probs, key=probs.get)
        prob = float(probs[top_lang])

        # Explicit transcribe
        res = model.transcribe(
            audio_path,
            fp16=False,
            task="transcribe",
            language=top_lang,
            temperature=0.0,
            condition_on_previous_text=False
        )
        elapsed = time.time() - t0
        raw_text = res.get("text", "").strip()

        comparison_table.append({
            "model": m_name,
            "detected_lang": top_lang,
            "probability": f"{prob:.4f}",
            "raw_transcript": raw_text,
            "time": f"{elapsed:.2f}s"
        })

    print(f"{'MODEL':<10} | {'DETECTED LANG':<15} | {'PROBABILITY':<12} | {'RAW TRANSCRIPT':<45} | {'TIME':<8}")
    print("-" * 100)
    for row in comparison_table:
        print(f"{row['model']:<10} | {row['detected_lang']:<15} | {row['probability']:<12} | {row['raw_transcript']:<45} | {row['time']:<8}")

    os.remove(audio_path)

def test_full_multilingual_pipeline():
    print("\n" + "=" * 60)
    print("FULL MULTILINGUAL PIPELINE VERIFICATION (BASE MODEL)")
    print("=" * 60)

    for lang_key, original_text in SENTENCES.items():
        print(f"\n--- Testing Language: {lang_key.upper()} ---")
        audio_path = generate_audio_file(original_text, lang_key)
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        t0 = time.time()
        res = transcribe_audio_bytes(audio_bytes, filename=f"test_{lang_key}.mp3")
        elapsed = time.time() - t0

        print(f"Elapsed Time: {elapsed:.2f}s")
        print(f"Result Dict: {res}")
        os.remove(audio_path)

if __name__ == "__main__":
    run_model_comparison_telugu()
    test_full_multilingual_pipeline()
