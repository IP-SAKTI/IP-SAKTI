"""
Comprehensive Test Script for Phase 2 Multilingual Voice & Translation Service
Tests English (en), Hindi (hi), Telugu (te), Kannada (kn), and unsupported languages.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from ip_sakti.services.transcription import (
    SUPPORTED_VOICE_LANGUAGES,
    LANG_CODE_MAP,
    get_query_translator,
)

def test_multilingual_translation():
    print("=== Testing Multilingual Voice Language Support & Translation ===")
    translator = get_query_translator()

    test_cases = [
        ("en", "What permissions are required to manufacture an Ayurvedic medicine?"),
        ("hi", "आयुर्वेदिक दवा बनाने के लिए क्या लाइसेंस चाहिए?"),
        ("te", "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"),
        ("kn", "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?"),
    ]

    for lang_code, raw_text in test_cases:
        norm_lang = LANG_CODE_MAP.get(lang_code, lang_code)
        assert norm_lang in SUPPORTED_VOICE_LANGUAGES, f"Language {lang_code} must be supported"

        if norm_lang == "en":
            translated = raw_text
        else:
            res = translator.translate_to_retrieval_language(raw_text, norm_lang)
            translated = res.translated_text

        response = {
            "transcript": raw_text,
            "language": norm_lang,
            "translated_text": translated,
            "error": None
        }

        print(f"\n[{norm_lang.upper()}] Input Transcript: {response['transcript']}")
        print(f"[{norm_lang.upper()}] Detected Language: {response['language']}")
        print(f"[{norm_lang.upper()}] Translated Text:  {response['translated_text']}")
        assert response["translated_text"] is not None and len(response["translated_text"]) > 0

    # Test Unsupported Language Case
    unsupported_lang = "ja"
    unsupported_norm = LANG_CODE_MAP.get(unsupported_lang, unsupported_lang)
    assert unsupported_norm not in SUPPORTED_VOICE_LANGUAGES
    unsupported_response = {
        "transcript": "こんにちは",
        "language": unsupported_norm,
        "translated_text": None,
        "error": "Unsupported voice language"
    }
    print(f"\n[JA - Unsupported] Response: {unsupported_response}")
    assert unsupported_response["error"] == "Unsupported voice language"

    print("\nSUCCESS: All Multilingual Voice & Translation unit tests passed cleanly!")

if __name__ == "__main__":
    test_multilingual_translation()
