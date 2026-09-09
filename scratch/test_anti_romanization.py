"""
Dedicated Anti-Romanization & Semantic Translation Test Suite
Ensures that transliterated/romanized strings like 'Hairovidha...' cause test failures,
while true semantic English translations pass.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from ip_sakti.services.transcription import is_romanized_gibberish, transcribe_audio_bytes
from ip_sakti.multilingual.translator import QueryTranslator

def test_anti_romanization():
    print("==================================================")
    print("ANTI-ROMANIZATION & TRUE SEMANTIC TRANSLATION TEST")
    print("==================================================\n")

    # 1. Test is_romanized_gibberish detector
    bad_romanized_string = "Hairovidha Haushdha Ni Hayaro Chi Tanki Hai Inhon Madho Kowali"
    good_english_string = "What permissions are required to manufacture Ayurvedic medicine?"

    print("--- 1. Testing Romanization Detector ---")
    assert is_romanized_gibberish(bad_romanized_string, "te") == True, "Must detect romanized gibberish as True"
    assert is_romanized_gibberish(good_english_string, "te") == False, "Must detect genuine English translation as False"
    print("  'Hairovidha...' detected as Romanized: TRUE (PASSED)")
    print("  'What permissions...' detected as Romanized: FALSE (PASSED)\n")

    # 2. Test True Semantic Translations for all 4 languages
    print("--- 2. Testing Semantic Translation Output for EN, HI, TE, KN ---")
    qt = QueryTranslator()
    
    cases = [
        {
            "lang": "te",
            "name": "Telugu",
            "input": "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?",
            "expected_keywords": ["permissions", "manufacture", "ayurvedic", "medicine"]
        },
        {
            "lang": "hi",
            "name": "Hindi",
            "input": "आयुर्वेदिक दवा बनाने के लिए क्या लाइसेंस चाहिए?",
            "expected_keywords": ["license", "make", "ayurvedic", "medicine"]
        },
        {
            "lang": "kn",
            "name": "Kannada",
            "input": "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?",
            "expected_keywords": ["permissions", "manufacture", "ayurvedic", "medicine"]
        },
        {
            "lang": "en",
            "name": "English",
            "input": "What permissions are required to manufacture an Ayurvedic medicine?",
            "expected_keywords": ["permissions", "manufacture", "ayurvedic", "medicine"]
        }
    ]

    for c in cases:
        if c["lang"] == "en":
            translated = c["input"]
        else:
            res = qt.translate_to_retrieval_language(c["input"], c["lang"])
            translated = res.translated_text

        print(f"[{c['name']}] ({c['lang'].upper()})")
        print(f"  Input Transcript: {c['input']}")
        print(f"  Translated Text:  {translated}")

        # Explicit Anti-Romanization Check
        assert not is_romanized_gibberish(translated, c["lang"]), f"FAIL: Returned romanized text instead of translation: {translated}"
        
        # Keyword semantic check
        translated_lower = translated.lower()
        found_words = [w for w in c["expected_keywords"] if w in translated_lower]
        assert len(found_words) > 0, f"FAIL: Translation lacks semantic English keywords: {translated}"
        print(f"  Matched Semantic Keywords: {found_words} (PASSED)\n")

    print("==================================================")
    print("✅ ALL ANTI-ROMANIZATION & TRANSLATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_anti_romanization()
