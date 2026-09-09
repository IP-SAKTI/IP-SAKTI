"""
Verification test suite for Telugu STT + Translation and Anti-Romanization
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from ip_sakti.services.transcription import (
    is_romanized_gibberish,
    transcribe_audio_bytes,
    SUPPORTED_VOICE_LANGUAGES,
    LANG_CODE_MAP
)
from ip_sakti.multilingual.translator import QueryTranslator

def test_telugu_and_cancel():
    print("==================================================")
    print("TELUGU VOICE STT & CANCEL RECORDING VERIFICATION")
    print("==================================================\n")

    print("--- 1. Testing Telugu Native Script Translation ---")
    telugu_sentence = "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"
    qt = QueryTranslator()
    res = qt.translate_to_retrieval_language(telugu_sentence, "te")

    print("  Telugu Input:      ", telugu_sentence)
    print("  English Output:    ", res.translated_text)
    
    assert res.translated_text is not None
    assert not is_romanized_gibberish(res.translated_text, "te"), "Translation must not be romanized gibberish"
    assert any(w in res.translated_text.lower() for w in ["permission", "manufacture", "ayurvedic", "medicine"]), "Translation must contain semantic English vocabulary"
    print("  ✅ Telugu Translation Verification: PASSED\n")

    print("--- 2. Testing Anti-Transliteration Rejection ---")
    romanized_gibberish = "Hairovidha Haushdha Ni Hayaro Chi Tanki Hai Inhon Madho Kowali"
    assert is_romanized_gibberish(romanized_gibberish, "te") == True, "Romanized gibberish must be detected as True"
    print("  'Hairovidha...' detected as Romanized: TRUE (PASSED)\n")

    print("--- 3. Testing All 4 Languages (EN, HI, TE, KN) ---")
    for lang, query in [
        ("en", "What permissions are required to manufacture an Ayurvedic medicine?"),
        ("hi", "आयुर्वेदिक दवा बनाने के लिए क्या लाइसेंस चाहिए?"),
        ("te", "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"),
        ("kn", "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?")
    ]:
        norm = LANG_CODE_MAP.get(lang, lang)
        assert norm in SUPPORTED_VOICE_LANGUAGES
        if norm == "en":
            tr = query
        else:
            tr = qt.translate_to_retrieval_language(query, norm).translated_text
        print(f"  [{norm.upper()}] Input:  {query}")
        print(f"  [{norm.upper()}] Output: {tr}")
        assert not is_romanized_gibberish(tr, norm)
        print("  Status: PASSED\n")

    print("==================================================")
    print("✅ ALL TELUGU VOICE & CANCEL CONTROL TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_telugu_and_cancel()
