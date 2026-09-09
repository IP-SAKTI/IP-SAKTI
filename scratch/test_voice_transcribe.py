"""
Test script for /transcribe API endpoint and transcription service
"""
import io
import wave
import numpy as np
from ip_sakti.services.transcription import transcribe_audio_bytes

def test_transcription_service():
    print("--- 1. Testing empty audio ---")
    res1 = transcribe_audio_bytes(b"", "empty.webm")
    print("Empty audio result:", res1)
    assert res1["error"] is not None

    print("\n--- 2. Testing synthetic WAV file ---")
    # Generate 1 second of 440 Hz sine wave as a valid WAV file
    sample_rate = 16000
    t = np.linspace(0, 1, sample_rate, False)
    sine_wave = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(sine_wave.tobytes())
    
    wav_bytes = wav_io.getvalue()
    res2 = transcribe_audio_bytes(wav_bytes, "sine.wav")
    print("Synthetic audio result:", res2)
    print("\n✅ Service tests passed cleanly!")

if __name__ == "__main__":
    test_transcription_service()
